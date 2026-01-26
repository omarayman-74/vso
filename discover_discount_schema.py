"""Discover discount/sale/offer related tables and columns in the database."""
import sys
import os

# Fix Windows encoding for emoji output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import mysql.connector
from config import settings

# Database configuration
DB_CONFIG = {
    "host": settings.db_host,
    "port": settings.db_port,
    "user": settings.db_user,
    "password": settings.db_password,
    "database": settings.db_name
}


def discover_discount_tables():
    """Search all tables for discount/sale/offer related columns."""
    print("\n" + "="*80)
    print("DATABASE SCHEMA DISCOVERY - DISCOUNT/SALE/OFFER TABLES")
    print("="*80 + "\n")
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        
        # Step 1: Get all tables
        print("Step 1: Getting all tables in database...")
        cursor.execute("SHOW TABLES")
        all_tables = [list(row.values())[0] for row in cursor.fetchall()]
        print(f"Found {len(all_tables)} tables\n")
        
        # Keywords to search for
        discount_keywords = ['discount', 'sale', 'offer', 'promo', 'promotion', 'deal', 'special']
        
        # Step 2: Find tables with discount-related names
        print("Step 2: Finding tables with discount-related names...")
        print("-" * 80)
        discount_tables = []
        for table in all_tables:
            table_lower = table.lower()
            if any(keyword in table_lower for keyword in discount_keywords):
                discount_tables.append(table)
                print(f"  [MATCH] {table}")
        
        if not discount_tables:
            print("  No tables found with discount-related names")
        print()
        
        # Step 3: Search all tables for discount-related columns
        print("Step 3: Searching all tables for discount-related columns...")
        print("-" * 80)
        
        tables_with_discount_columns = {}
        
        for table in all_tables:
            try:
                cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                columns = cursor.fetchall()
                
                # Check if table has unit_id column
                has_unit_id = any(col['Field'].lower() == 'unit_id' for col in columns)
                
                # Find discount-related columns
                discount_columns = []
                for col in columns:
                    col_name_lower = col['Field'].lower()
                    if any(keyword in col_name_lower for keyword in discount_keywords):
                        discount_columns.append({
                            'name': col['Field'],
                            'type': col['Type'],
                            'null': col['Null'],
                            'key': col['Key'],
                            'default': col['Default']
                        })
                
                if discount_columns:
                    tables_with_discount_columns[table] = {
                        'has_unit_id': has_unit_id,
                        'columns': discount_columns,
                        'total_columns': len(columns)
                    }
                    
                    print(f"\n  TABLE: {table}")
                    print(f"    Has unit_id: {'YES' if has_unit_id else 'NO'}")
                    print(f"    Total columns: {len(columns)}")
                    print(f"    Discount-related columns:")
                    for dcol in discount_columns:
                        print(f"      - {dcol['name']} ({dcol['type']}) [Null: {dcol['null']}, Key: {dcol['key'] or 'None'}]")
                
            except Exception as e:
                print(f"  [ERROR] Cannot query table {table}: {str(e)}")
        
        if not tables_with_discount_columns:
            print("  No discount-related columns found in any table")
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total tables: {len(all_tables)}")
        print(f"Tables with discount-related names: {len(discount_tables)}")
        print(f"Tables with discount-related columns: {len(tables_with_discount_columns)}")
        
        # Step 4: Sample data from discount tables
        print("\n" + "="*80)
        print("SAMPLE DATA FROM DISCOUNT TABLES")
        print("="*80)
        
        for table, info in tables_with_discount_columns.items():
            if info['has_unit_id']:
                print(f"\n  TABLE: {table}")
                try:
                    # Get sample rows
                    cursor.execute(f"SELECT * FROM `{table}` LIMIT 3")
                    sample_rows = cursor.fetchall()
                    
                    if sample_rows:
                        print(f"    Showing {len(sample_rows)} sample row(s):")
                        for idx, row in enumerate(sample_rows, 1):
                            print(f"\n    Row {idx}:")
                            for key, value in row.items():
                                if value is not None and str(value).strip():
                                    # Only show non-empty values
                                    print(f"      {key}: {value}")
                    else:
                        print("    No data in this table")
                        
                except Exception as e:
                    print(f"    [ERROR] Cannot query data: {str(e)}")
        
        cursor.close()
        connection.close()
        
        print("\n" + "="*80)
        print("DISCOVERY COMPLETE")
        print("="*80 + "\n")
        
        # Return results for programmatic use
        return {
            'all_tables': all_tables,
            'discount_tables': discount_tables,
            'tables_with_discount_columns': tables_with_discount_columns
        }
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    discover_discount_tables()
