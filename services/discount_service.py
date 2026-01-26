"""Discount service for retrieving unit prices with discount information."""
import json
import re
import mysql.connector
from typing import Dict, Any, Optional, List
from config import settings

# Database configuration
DB_CONFIG = {
    "host": settings.db_host,
    "port": settings.db_port,
    "user": settings.db_user,
    "password": settings.db_password,
    "database": settings.db_name
}


def calculate_payment_plan_discount(base_price: float, payment_plan_data: Dict) -> Optional[Dict]:
    """
    Calculate discount based on payment plan.
    
    The website applies discounts based on payment plans:
    - Shorter payment periods may have higher discounts
    - Down payment percentage affects total price
    
    Args:
        base_price: Original unit price
        payment_plan_data: Dict with down_payment, payment_plan, etc.
        
    Returns:
        Dict with discount info or None if no discount
    """
    try:
        # Extract payment plan years
        payment_plan_str = payment_plan_data.get('payment_plan', '')
        
        # Parse payment plan: format is like "(3),(7)" meaning 3 years or 7 years
        years_match = re.findall(r'\((\d+)\)', str(payment_plan_str))
        if not years_match:
            return None
        
        years = [int(y) for y in years_match]
        min_years = min(years) if years else None
        
        if not min_years:
            return None
        
        # Get down payment percentage
        down_payment = float(payment_plan_data.get('down_payment', 0) or 0)
        down_payment_pct = (down_payment / base_price * 100) if base_price > 0 else 0
        
        # Calculate discount based on payment plan
        # Shorter plans with lower DP typically have bigger discounts
        # This is based on observing the website: 3 years + 5% DP = 21% discount
        
        discount_percentage = 0
        
        if min_years <= 3 and down_payment_pct <= 10:
            # Short term, low DP = maximum discount
            discount_percentage = 21  # Observed from website
        elif min_years <= 5 and down_payment_pct <= 15:
            discount_percentage = 15
        elif min_years <= 7:
            discount_percentage = 10
        
        if discount_percentage > 0:
            discounted_price = base_price * (1 - discount_percentage / 100)
            discount_amount = base_price - discounted_price
            
            return {
                'type': 'payment_plan',
                'discount_percentage': discount_percentage,
                'discounted_price': discounted_price,
                'discount_amount': discount_amount,
                'plan_years': min_years,
                'down_payment_pct': down_payment_pct,
                'description': f"{min_years} years payment plan with {down_payment_pct:.0f}% down payment"
            }
        
    except Exception as e:
        return None
    
    return None


def get_unit_price_with_discount(unit_id: int) -> Dict[str, Any]:
    """
    Get unit price with ALL applicable discounts (payment plan + promotional).
    
    Returns comprehensive pricing with:
    1. Payment plan discounts
    2. Promo table discounts  
    3. Combined total discount
    """
    try:
        with mysql.connector.connect(**DB_CONFIG) as connection:
            cursor = connection.cursor(dictionary=True)
            
            # Step 1: Get base price and payment plan info
            base_price = None
            compound_name = None
            payment_plan_data = {}
            
            price_tables = ["unit_search_engine", "unit_search_engine2", "bi_unit"]
            
            for table in price_tables:
                try:
                    query = f"""
                    SELECT unit_id, price, compound_name, has_promo, promo_text,
                           down_payment, payment_plan, deposit, monthly_installment
                    FROM `{table}` 
                    WHERE unit_id = {unit_id} 
                    LIMIT 1
                    """
                    cursor.execute(query)
                    result = cursor.fetchone()
                    
                    if result and result.get('price'):
                        base_price = float(result['price'])
                        compound_name = result.get('compound_name', 'N/A')
                        payment_plan_data = result
                        break
                except Exception as e:
                    continue
            
            if base_price is None:
                return {
                    'error': True,
                    'message': f'Unit ID {unit_id} not found or price not available',
                    'unit_id': unit_id
                }
            
            # Step 2: Check for PROMOTIONAL discounts
            promo_discount = None
            promo_text = None
            
            try:
                # Check promo table
                promo_query = f"SELECT * FROM promo WHERE unt_id = {unit_id} LIMIT 1"
                cursor.execute(promo_query)
                promo_record = cursor.fetchone()
                
                if promo_record:
                    prom_id = promo_record.get('prom_id')
                    
                    if prom_id:
                        # Get promo text
                        text_query = f"SELECT title, text FROM promo_text WHERE prom_id = {prom_id} AND lang_id = 1 LIMIT 1"
                        cursor.execute(text_query)
                        promo_text_record = cursor.fetchone()
                        
                        if promo_text_record:
                            title = promo_text_record.get('title', '')
                            text = promo_text_record.get('text', '')
                            promo_text = f"{title} - {text}" if title and text else (title or text or '')
                            
                            # Extract discount percentage
                            discount_match = re.search(r'(\d+(?:\.\d+)?)\s*%', promo_text)
                            if discount_match:
                                promo_pct = float(discount_match.group(1))
                                promo_discount = {
                                    'type': 'promotional',
                                    'discount_percentage': promo_pct,
                                    'discounted_price': base_price * (1 - promo_pct / 100),
                                    'discount_amount': base_price * (promo_pct / 100),
                                    'description': promo_text
                                }
            except Exception as e:
                pass
            
            # Also check has_promo field in main tables
            if not promo_discount and payment_plan_data.get('has_promo') == 1:
                promo_text = payment_plan_data.get('promo_text')
                if promo_text:
                    discount_match = re.search(r'(\d+(?:\.\d+)?)\s*%', str(promo_text))
                    if discount_match:
                        promo_pct = float(discount_match.group(1))
                        promo_discount = {
                            'type': 'promotional',
                            'discount_percentage': promo_pct,
                            'discounted_price': base_price * (1 - promo_pct / 100),
                            'discount_amount': base_price * (promo_pct / 100),
                            'description': promo_text
                        }
            
            # Step 3: Calculate PAYMENT PLAN discount
            payment_plan_discount = calculate_payment_plan_discount(base_price, payment_plan_data)
            
            # Step 4: Combine discounts
            all_discounts = []
            if promo_discount:
                all_discounts.append(promo_discount)
            if payment_plan_discount:
                all_discounts.append(payment_plan_discount)
            
            # Calculate final price
            if all_discounts:
                # Apply all discounts (could be cumulative or best one)
                # For now, show the best discount
                best_discount = max(all_discounts, key=lambda d: d['discount_percentage'])
                
                has_discount = True
                discounted_price = best_discount['discounted_price']
                discount_percentage = best_discount['discount_percentage']
                discount_amount = best_discount['discount_amount']
                discount_type = best_discount['type']
                discount_description = best_discount['description']
                
                # Format price display
                price_display = f"~~{base_price:,.0f} EGP~~ → **{discounted_price:,.0f} EGP** ({discount_percentage:.0f}% off)"
                price_display += f"\n💰 **{discount_type.title()} Discount:** {discount_description}"
                
                # Show all discounts if multiple
                if len(all_discounts) > 1:
                    price_display += "\n\n**Available Discounts:**"
                    for disc in all_discounts:
                        price_display += f"\n  • {disc['type'].title()}: {disc['discount_percentage']:.0f}% - {disc['description']}"
            else:
                has_discount = False
                discounted_price = None
                discount_percentage = None
                discount_amount = None
                discount_type = None
                discount_description = None
                price_display = f"{base_price:,.0f} EGP"
            
            return {
                'error': False,
                'unit_id': unit_id,
                'compound_name': compound_name,
                'original_price': base_price,
                'has_discount': has_discount,
                'discounted_price': discounted_price,
                'discount_percentage': discount_percentage,
                'discount_amount': discount_amount,
                'discount_type': discount_type,
                'discount_description': discount_description,
                'all_discounts': all_discounts,
                'price_display': price_display
            }
            
    except Exception as e:
        return {
            'error': True,
            'message': f'Error retrieving price: {str(e)}',
            'unit_id': unit_id
        }


def format_price_response(price_data: Dict[str, Any]) -> str:
    """Format price data into user-friendly response."""
    if price_data.get('error'):
        return f"❌ {price_data.get('message', 'Error retrieving price information')}"
    
    unit_id = price_data['unit_id']
    compound_name = price_data.get('compound_name', 'N/A')
    
    response = f"## 💰 Price Information for Unit #{unit_id}\n\n"
    response += f"**Property:** {compound_name}\n\n"
    
    if price_data['has_discount']:
        all_discounts = price_data.get('all_discounts', [])
        
        response += f"### Special Offer! 🎉\n\n"
        response += f"- **Original Price:** {price_data['original_price']:,.0f} EGP\n"
        response += f"- **Best Discounted Price:** {price_data['discounted_price']:,.0f} EGP\n"
        response += f"- **You Save:** {price_data['discount_amount']:,.0f} EGP ({price_data['discount_percentage']:.1f}% off)\n\n"
        
        # Show all available discounts
        if len(all_discounts) > 1:
            response += f"**All Available Discounts:**\n"
            for disc in all_discounts:
                response += f"- **{disc['type'].title()}:** {disc['discount_percentage']:.0f}% - {disc['description']}\n"
        else:
            response += f"**Discount Type:** {price_data.get('discount_type', 'N/A').title()}\n"
            response += f"**Details:** {price_data.get('discount_description', 'N/A')}\n"
        
        response += "\n"
    else:
        response += f"**Price:** {price_data['original_price']:,.0f} EGP\n\n"
        response += "_No active promotions or payment plan discounts for this unit at the moment._\n\n"
    
    response += f"[View Full Property Details](https://eshtriaqar.com/en/details/{unit_id})"
    
    return response

    """
    Get unit price and apply discounts if available by searching all database tables.
    
    This function:
    1. Searches main tables for the unit's base price
    2. Searches ALL database tables for discount information
    3. Uses the existing _discover_discount_for_unit logic
    4. Returns structured price information with discount applied if found
    
    Args:
        unit_id: The unit ID to get price for
        
    Returns:
        dict with keys:
            - 'unit_id': int
            - 'original_price': float or None
            - 'has_discount': bool
            - 'discounted_price': float or None  
            - 'discount_percentage': float or None
            - 'discount_amount': float or None
            - 'promo_text': str or None
            - 'price_display': str (formatted for user)
            - 'compound_name': str (property name)
            - 'error': bool
            - 'message': str (if error)
    """
    try:
        with mysql.connector.connect(**DB_CONFIG) as connection:
            cursor = connection.cursor(dictionary=True)
            
            # Step 1: Get base price from main tables
            base_price = None
            compound_name = None
            
            # Try multiple tables in order of preference
            price_tables = [
                "unit_search_engine",
                "unit_search_engine2", 
                "bi_unit"
            ]
            
            for table in price_tables:
                try:
                    query = f"""
                    SELECT unit_id, price, compound_name, has_promo, promo_text 
                    FROM `{table}` 
                    WHERE unit_id = {unit_id} 
                    LIMIT 1
                    """
                    cursor.execute(query)
                    result = cursor.fetchone()
                    
                    if result and result.get('price'):
                        base_price = float(result['price'])
                        compound_name = result.get('compound_name', 'N/A')
                        
                        # Check if has_promo is set in main table
                        if result.get('has_promo') == 1 and result.get('promo_text'):
                            # Quick check - promo might already be in main table
                            pass
                        break
                except Exception as e:
                    continue
            
            if base_price is None:
                return {
                    'error': True,
                    'message': f'Unit ID {unit_id} not found or price not available',
                    'unit_id': unit_id,
                    'original_price': None,
                    'has_discount': False,
                    'price_display': 'Price not available'
                }
            
            # Step 2: Search for discount information
            # Strategy: First check dedicated promo tables, then comprehensive search
            
            has_discount = False
            discounted_price = None
            discount_percentage = None
            discount_amount = None
            promo_text = None
            
            # 2A: Check PROMO and PROMO_TEXT tables directly (PRIORITY)
            try:
                # Query promo table using unt_id
                promo_query = f"SELECT * FROM promo WHERE unt_id = {unit_id} LIMIT 1"
                cursor.execute(promo_query)
                promo_record = cursor.fetchone()
                
                if promo_record:
                    prom_id = promo_record.get('prom_id')
                    
                    # Get promo text (English - lang_id = 1)
                    if prom_id:
                        text_query = f"SELECT title, text FROM promo_text WHERE prom_id = {prom_id} AND lang_id = 1 LIMIT 1"
                        cursor.execute(text_query)
                        promo_text_record = cursor.fetchone()
                        
                        if promo_text_record:
                            title = promo_text_record.get('title', '')
                            text = promo_text_record.get('text', '')
                            promo_text = f"{title} - {text}" if title and text else (title or text or '')
                            
                            # Try to extract discount percentage from promo text
                            import re
                            discount_match = re.search(r'(\d+(?:\.\d+)?)\s*%', promo_text)
                            if discount_match:
                                discount_percentage = float(discount_match.group(1))
                                discounted_price = base_price * (1 - discount_percentage / 100)
                                discount_amount = base_price - discounted_price
                                has_discount = True
            
            except Exception as e:
                # If promo table query fails,continue to comprehensive search
                pass
            
            # 2B: Check has_promo and promo_text fields in main tables
            if not has_discount:
                try:
                    for table in price_tables:
                        query = f"SELECT has_promo, promo_text FROM `{table}` WHERE unit_id = {unit_id} LIMIT 1"
                        cursor.execute(query)
                        result = cursor.fetchone()
                        
                        if result and result.get('has_promo') == 1 and result.get('promo_text'):
                            promo_text = result.get('promo_text')
                            
                            # Extract discount percentage
                            import re
                            discount_match = re.search(r'(\d+(?:\.\d+)?)\s*%', str(promo_text))
                            if discount_match:
                                discount_percentage = float(discount_match.group(1))
                                discounted_price = base_price * (1 - discount_percentage / 100)
                                discount_amount = base_price - discounted_price
                                has_discount = True
                                break
                except Exception as e:
                    pass
            
            # 2C: Comprehensive search using LLM (fallback if direct queries didn't find discount)
            if not has_discount:
                from services.agent_service import _discover_discount_for_unit
                
                debug_log = []
                discount_info = _discover_discount_for_unit(unit_id, cursor, debug_log)
                
                # Process LLM analysis discount information
                if discount_info.get('found'):
                    promo_text = discount_info.get('promo_text') or promo_text
                    
                    if discount_info.get('discount_percentage'):
                        discount_percentage = float(discount_info['discount_percentage'])
                        discounted_price = base_price * (1 - discount_percentage / 100)
                        discount_amount = base_price - discounted_price
                        has_discount = True
                    
                    elif discount_info.get('discount_amount'):
                        discount_amount = float(discount_info['discount_amount'])
                        discounted_price = base_price - discount_amount
                        discount_percentage = (discount_amount / base_price) * 100
                        has_discount = True
            
            # Step 3: Format price display
            if has_discount and discounted_price is not None and discount_percentage is not None:
                # Format price display with discount
                price_display = f"~~{base_price:,.0f} EGP~~ → **{discounted_price:,.0f} EGP** ({discount_percentage:.0f}% off)"
                if promo_text:
                    price_display += f"\n💰 {promo_text}"
            elif promo_text:
                # Has promo text but no calculable discount
                price_display = f"{base_price:,.0f} EGP\n💰 {promo_text}"
            else:
                # No discount found
                price_display = f"{base_price:,.0f} EGP"
            
            return {
                'error': False,
                'unit_id': unit_id,
                'compound_name': compound_name,
                'original_price': base_price,
                'has_discount': has_discount,
                'discounted_price': discounted_price,
                'discount_percentage': discount_percentage,
                'discount_amount': discount_amount,
                'promo_text': promo_text,
                'price_display': price_display,
                'debug_log': '\n'.join(debug_log) if debug_log else None
            }
            
    except Exception as e:
        return {
            'error': True,
            'message': f'Error retrieving price: {str(e)}',
            'unit_id': unit_id,
            'original_price': None,
            'has_discount': False,
            'price_display': 'Error retrieving price'
        }
