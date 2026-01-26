"""Chat service for orchestrating agent interactions."""
import json
import re
import os
import sys
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.agent_service import SessionMemory, create_agent, now_ts, guard_agent
from services.language_service import detect_language, translate_text_logic_func
from services.database_service import safe_serialize
from config import settings

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chat_log.txt")

def safe_print(message):
    """
    Safely print messages to console, handling Unicode encoding errors on Windows.
    Falls back to ASCII representation if Unicode fails.
    """
    try:
        print(message)
    except UnicodeEncodeError:
        # Try encoding with errors='replace' to replace problematic characters
        try:
            safe_msg = message.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8')
            print(safe_msg)
        except:
            # Last resort: ASCII representation
            print(message.encode('ascii', errors='replace').decode('ascii'))

def log_full_action(user_query, bot_reply, session_memory, agent_name="Main Agent", execution_time=None):
    """
    Logs one full chat turn in a human-readable txt file.
    Includes user query, SQL, RAG, evaluation, and bot reply in one block.
    """
    timestamp = now_ts()
    
    # Determine the path from agent_name
    path = "CHAT"
    if "SQL" in agent_name:
        path = "SQL"
    elif "RAG" in agent_name:
        path = "RAG"
    elif "Guard" in agent_name:
        path = "GUARD"
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}]\n")
        f.write(f"Path: {path}\n")
        f.write(f"Agent: {agent_name}\n")
        f.write(f"User: {user_query}\n")
        if execution_time is not None:
            f.write(f"Response Time: {execution_time:.3f} seconds\n")
        
        # Access session_memory attributes safely (it is an object, not a dict)
        safety_check = getattr(session_memory, "safety_check", None)
        if safety_check:
            f.write(f"Safety Check: {safety_check}\n")
            
        last_sql = getattr(session_memory, "last_sql", None)
        if last_sql:
            f.write(f"SQL: {last_sql}\n")
            
        last_eval = getattr(session_memory, "last_eval", None)
        if last_eval:
            f.write(f"SQL Evaluator: {last_eval}\n")
            
        last_rag_results = getattr(session_memory, "last_rag_results", None)
        if last_rag_results:
            # Handle list vs string
            rag_preview = str(last_rag_results)[:200]
            f.write(f"RAG Results: {rag_preview}...\n")
            
        last_rag_eval = getattr(session_memory, "last_rag_eval", None)
        if last_rag_eval:
            f.write(f"RAG Evaluator: {last_rag_eval}\n")
            
        agent_communications = getattr(session_memory, "agent_communications", [])
        if agent_communications:
            f.write(f"Agent Communications: {agent_communications[-3:]}\n")
            
        f.write(f"Bot: {bot_reply}\n")
        f.write("="*60 + "\n\n")

def save_sql_to_file(sql_query: str):
    """Save generated SQL to a file in the queries directory."""
    try:
        queries_dir = "queries"
        if not os.path.exists(queries_dir):
            os.makedirs(queries_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{queries_dir}/query_{timestamp}_{unique_id}.sql"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(sql_query)
            
    except Exception as e:
        safe_print(f"Error saving SQL to file: {e}")

# ... inside ChatService class ...

class ChatService:
    """Service for handling chat interactions."""
    
    def __init__(self):
        """Initialize chat service."""
        self.sessions: Dict[str, SessionMemory] = {}
    
    def get_or_create_session(self, session_id: str) -> SessionMemory:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMemory()
        return self.sessions[session_id]

    def process_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Process user message and return response.
        
        Returns:
            Dict with keys: response, sql_logs
        """
        session_memory = self.get_or_create_session(session_id)
        
        # 🚀 PERFORMANCE: Check cache first (before any processing)
        from services.cache_service import response_cache
        
        # Try to get language from session, default to 'en' for first query
        cache_language = getattr(session_memory, 'detected_language', 'en') or 'en'
        cached_response = response_cache.get(message, cache_language)
        
        if cached_response:
            # Return cached response immediately
            return cached_response
        
        # 🛡️ SECURITY CHECK FIRST
        guard_start_time = time.time()
        security_check = guard_agent(message)
        guard_execution_time = time.time() - guard_start_time
        
        if not security_check.get("safe", True):
            refusal_msg = "I cannot process this request due to safety guidelines."
            if "reason" in security_check:
                 safe_print(f"WARNING: Security Violation Blocked: {security_check['reason']}")
            
            # Log violation with execution time
            log_full_action(message, refusal_msg, session_memory, agent_name="Guard Agent", execution_time=guard_execution_time)
            
            return {
                "response": refusal_msg,
                "sql_logs": []
            }
        
        # Reset new_results check for this turn
        session_memory.new_results_fetched = False
        session_memory.rag_used = False
        session_memory.payment_plan_used = False
        
        # 🌍 LANGUAGE DETECTION
        try:
            language_result_json = detect_language(message)
            # Parse JSON if needed (the new service returns a JSON string or dict depending on how it's called, 
            # but detect_language_logic returns a JSON string or Dict? Let's check language_service.py again.
            # In step 193, detect_language_logic returns json.dumps(...) -> string.
            if isinstance(language_result_json, str):
                try:
                    language_result = json.loads(language_result_json)
                except:
                    language_result = {"language": "en"}
            else:
                 language_result = language_result_json
            
            # DEBUG PRINT
            safe_print(f"[DEBUG] Language Raw JSON: {str(language_result)[:100]}")
            
            detected_lang = language_result.get("language", "en")
            session_memory.detected_language = detected_lang
            session_memory.language_confidence = language_result.get("confidence", "medium")
            
            safe_print(f"Language detected: {detected_lang}")
            
        except Exception as e:
            safe_print(f"Language detection error: {e}, defaulting to English")
            session_memory.detected_language = "en"
            session_memory.language_confidence = "low"
        
        # Add to chat history
        session_memory.chat_history.append({
            "role": "user",
            "content": message,
            "timestamp": now_ts()
        })
        
        # Store current query for context access
        session_memory.current_query = message
        
        
        # ═══════════════════════════════════════════════════════════════
        # PRE-PROCESSING: Semantic Intent Classification for Project Queries
        # ═══════════════════════════════════════════════════════════════
        # This uses LLM to semantically classify intent, not keyword matching
        
        def classify_query_intent(query: str) -> dict:
            """
            Use LLM to semantically classify the user's intent.
            Returns: dict with 'intent' and 'confidence'
            
            This is NOT keyword matching - it's semantic understanding.
            """
            from services.agent_service import _get_llm
            llm = _get_llm()
            
            classification_prompt = f"""You are an intent classifier for a real estate chatbot.

User Query: "{query}"

Classify this query into EXACTLY ONE of these categories:

1. **project_info** - User wants INFORMATION ABOUT what projects exist/are available
   - Asking WHICH/WHAT projects can be purchased
   - Wants to LEARN about project options
   - NOT searching for specific units with criteria
   Example: "What projects are available?", "Tell me about X project", "ايه المشاريع المتاحة"

2. **unit_search** - User wants to SEARCH/FIND specific units with filtering criteria
   - Has requirements (rooms, price, area, location)
   - Wants to see SPECIFIC units matching their needs
   Example: "Find 4 bedroom apartment", "Units under 2M", "3 rooms in Madinaty"

3. **other** - General questions, greetings, policies, or anything else

Think about the USER'S GOAL, not specific words used.

Respond with ONLY valid JSON:
{{
  "intent": "project_info" or "unit_search" or "other",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

            try:
                response = llm.invoke(classification_prompt).content.strip()
                # Clean JSON formatting
                response = response.replace('```json', '').replace('```', '').strip()
                
                # Parse JSON
                import json
                parsed = json.loads(response)
                
                return {
                    'intent': parsed.get('intent', 'other'),
                    'confidence': parsed.get('confidence', 0.5),
                    'reasoning': parsed.get('reasoning', '')
                }
            except Exception as e:
                safe_print(f"[INTENT CLASSIFIER] Error: {e}")
                return {'intent': 'other', 'confidence': 0.0, 'reasoning': 'Error'}
        
        def validate_routing_decision(query: str, initial_decision: str) -> dict:
            """
            Validation function to double-check routing decision when confidence is low.
            Called only when confidence < 75%.
            
            Args:
                query: User's original query
                initial_decision: The initial routing decision (project_info, unit_search, other)
            
            Returns:
                dict with 'confirmed_intent', 'should_override', 'reasoning'
            """
            from services.agent_service import _get_llm
            llm = _get_llm()
            
            validation_prompt = f"""You are a routing validator for a real estate chatbot.

The system initially classified this query as: "{initial_decision}"

User Query: "{query}"

Your job is to VALIDATE if this routing decision is correct.

**Routing Options:**
- **project_info**: User wants to know WHICH projects are available (general info)
- **unit_search**: User wants to FIND specific units with criteria (search)
- **other**: General chat, policies, greetings

Is the initial decision CORRECT?

Respond with ONLY valid JSON:
{{
  "is_correct": true or false,
  "correct_intent": "project_info" or "unit_search" or "other",
  "reasoning": "why you agree or disagree"
}}"""

            try:
                response = llm.invoke(validation_prompt).content.strip()
                response = response.replace('```json', '').replace('```', '').strip()
                
                import json
                parsed = json.loads(response)
                
                return {
                    'confirmed_intent': parsed.get('correct_intent', initial_decision),
                    'should_override': not parsed.get('is_correct', True),
                    'reasoning': parsed.get('reasoning', '')
                }
            except Exception as e:
                safe_print(f"[ROUTING VALIDATOR] Error: {e}")
                return {
                    'confirmed_intent': initial_decision,
                    'should_override': False,
                    'reasoning': 'Validation failed, using initial decision'
                }
        
        # Classify the query intent with confidence (for logging purposes only)
        if settings.enable_intent_classifier:
            classification_result = classify_query_intent(message)
            intent = classification_result['intent']
            confidence = classification_result['confidence']
            
            safe_print(f"[INTENT CLASSIFIER] Query: '{message[:50]}...' -> Intent: {intent} (confidence: {confidence:.2%})")
            safe_print(f"[INFO] Sending to orchestrator for routing decision...")
        else:
            # Skip intent classification for performance
            classification_result = {'intent': 'unknown', 'confidence': 1.0, 'reasoning': 'Classifier disabled'}
            intent = 'unknown'
            confidence = 1.0
            safe_print(f"[INTENT CLASSIFIER] DISABLED - Skipping for performance")
            safe_print(f"[INFO] Sending directly to orchestrator...")
        
        # Continue with normal orchestrator flow
        # Create agent
        agent_executor = create_agent(session_memory)

        
        # Prepare chat history for agent
        chat_history = []
        for msg in session_memory.chat_history[-10:]:  # Last 10 messages
            if msg["role"] == "user":
                chat_history.append(("human", msg["content"]))
            else:
                chat_history.append(("assistant", msg["content"]))
        
        try:
            # ⏱️ Start timing
            start_time = time.time()
            
            # Invoke agent
            result = agent_executor.invoke({
                "input": message,
                "chat_history": chat_history
            })
            
            # ⏱️ Calculate execution time
            execution_time = time.time() - start_time
            
            
            response_text = result.get("output", "I apologize, but I couldn't process your request.")
            
            # Post-process to remove unwanted image sections
            response_text = self._clean_image_sections(response_text)
            
            # Determine Actual Agent Used by orchestrator
            actual_agent = "Chat Agent"
            orchestrator_route = "chat"
            
            # Check payment plan first (it sets both payment_plan_used AND sql_agent_used)
            if getattr(session_memory, "payment_plan_used", False):
                 actual_agent = "SQL Search Agent (Payment Plan)"
                 orchestrator_route = "sql"
            elif getattr(session_memory, "sql_agent_used", False):
                 actual_agent = "SQL Search Agent"
                 orchestrator_route = "sql"
            elif getattr(session_memory, "rag_agent_used", False):
                 actual_agent = "RAG Knowledge Agent"
                 orchestrator_route = "rag"
            elif getattr(session_memory, "chat_agent_used", False):
                 actual_agent = "Chat Agent"
                 orchestrator_route = "chat"
            
            safe_print(f"[ORCHESTRATOR] Routing decision: {orchestrator_route.upper()}")
            
            # 🔍 CROSS-VALIDATION: Compare pre-classifier with orchestrator decision
            # Map intent to route for comparison
            intent_to_route = {
                'project_info': 'rag',
                'unit_search': 'sql',
                'other': 'chat'
            }
            expected_route = intent_to_route.get(intent, 'chat')
            
            # Check if cross-validation is enabled (disabled by default for performance)
            if settings.enable_cross_validation:
                # Determine if we need to re-invoke orchestrator
                is_mismatch = (expected_route != orchestrator_route)
                is_low_confidence = (confidence < 0.70)
                
                # Three scenarios:
                # 1. Match + High Confidence → Execute directly
                # 2. Mismatch (any confidence) → Re-invoke
                # 3. Match + Low Confidence → Re-invoke
                needs_validation = is_mismatch or is_low_confidence
            else:
                # Cross-validation disabled for performance
                needs_validation = False
                safe_print(f"[VALIDATION] DISABLED - Trusting orchestrator decision: {orchestrator_route.upper()}")
            
            if needs_validation:
                # Determine reason for validation
                if is_mismatch:
                    safe_print(f"[VALIDATION] 🚨 MISMATCH DETECTED!")
                    safe_print(f"[VALIDATION]   Pre-classifier predicted: {expected_route.upper()} (confidence: {confidence:.2%})")
                    safe_print(f"[VALIDATION]   Orchestrator decided: {orchestrator_route.upper()}")
                    validation_reason = "disagreement between pre-classifier and orchestrator"
                else:
                    safe_print(f"[VALIDATION] ⚠️ LOW CONFIDENCE MATCH!")
                    safe_print(f"[VALIDATION]   Both chose: {orchestrator_route.upper()}")
                    safe_print(f"[VALIDATION]   But confidence is low: {confidence:.2%}")
                    validation_reason = f"low confidence ({confidence:.2%}) despite agreement"
                
                safe_print(f"[VALIDATION]   Re-invoking orchestrator due to {validation_reason}...")
                
                # Reset agent flags before retry
                session_memory.sql_agent_used = False
                session_memory.rag_agent_used = False
                session_memory.chat_agent_used = False
                
                # Create validation message with structured context
                if is_mismatch:
                    validation_message = f"""[ROUTING VALIDATION REQUIRED]

{{
  "original_query": "{message}",
  "pre_classifier": {{
    "decision": "{expected_route.upper()}",
    "confidence": {confidence:.2f},
    "reasoning": "{classification_result.get('reasoning', 'N/A')}"
  }},
  "orchestrator_first_decision": "{orchestrator_route.upper()}",
  "validation_type": "MISMATCH"
}}

The pre-classifier and orchestrator disagreed on routing.
Please re-evaluate this query and make your FINAL decision: SQL, RAG, or CHAT.
Then respond to the original user query."""
                else:
                    validation_message = f"""[ROUTING VALIDATION REQUIRED]

{{
  "original_query": "{message}",
  "pre_classifier": {{
    "decision": "{expected_route.upper()}",
    "confidence": {confidence:.2f},
    "reasoning": "{classification_result.get('reasoning', 'N/A')}"
  }},
  "orchestrator_first_decision": "{orchestrator_route.upper()}",
  "validation_type": "LOW_CONFIDENCE_MATCH"
}}

Both agreed on {orchestrator_route.upper()}, but confidence is low ({confidence:.2%}).
Please re-evaluate with extra care and confirm your FINAL decision: SQL, RAG, or CHAT.
Then respond to the original user query."""
                
                # Re-invoke orchestrator with validation context
                retry_start = time.time()
                retry_result = agent_executor.invoke({
                    "input": validation_message,
                    "chat_history": chat_history
                })
                retry_time = time.time() - retry_start
                
                # Update response and routing
                response_text = retry_result.get("output", response_text)
                response_text = self._clean_image_sections(response_text)
                
                # Determine final routing after retry
                if getattr(session_memory, "sql_agent_used", False):
                    final_route = "sql"
                    actual_agent = "SQL Search Agent"
                elif getattr(session_memory, "rag_agent_used", False):
                    final_route = "rag"
                    actual_agent = "RAG Knowledge Agent"
                else:
                    final_route = "chat"
                    actual_agent = "Chat Agent"
                
                safe_print(f"[VALIDATION] ✅ Final decision after retry: {final_route.upper()}")
                safe_print(f"[VALIDATION] Retry time: {retry_time:.2f}s")
                
                # Update total execution time
                execution_time += retry_time
            else:
                # High confidence match - proceed directly
                safe_print(f"[VALIDATION] ✅ Strong agreement: Both chose {orchestrator_route.upper()} (confidence: {confidence:.2%})")
                safe_print(f"[VALIDATION] Proceeding without validation")


            
            # (Logging moved to end of function to capture final output)
            
            # Result processing and Agent Logic

            
            # ---------------------------------------------------------
            # CAROUSEL INJECTION LOGIC
            # ---------------------------------------------------------
            # Only show carousel if NEW results were fetched this turn
            # AND it's not a detail request for a single unit already shown
            
            # Detect if this is a detail request (user clicked "Ask Details" or similar)
            is_detail_request = False
            message_lower = message.lower()
            
            # Phrase detection for detail requests (English, Arabic, Franco)
            detail_phrases = [
                'retrieve full details', 'tell me more about', 'details for unit', # EN
                'تفاصيل أكتر عن', 'قولي تفاصيل', 'اسأل عن التفاصيل', 'عايز تفاصيل', # AR
                'tafaseel aktr', '2oly tafaseel', 'esa2al 3an el tafaseel', '3ayez tafaseel', # Franco
                'وريني التفاصيل', 'شوفت التفاصيل', 'اعرف اكتر', 'عايز اعرف', 'هات التفاصيل' # Additional Arabic
            ]
            
            if any(phrase in message_lower for phrase in detail_phrases) or re.search(r'(?:unit|الوحدة|unit ra2am|unit #|رقم)\s*(?:number|رقم)?\s*#?(\d+)', message_lower):
                # Check if asking about a single unit that was recently shown
                if session_memory.last_results and len(session_memory.last_results) >= 1:
                    # If we have previous results and this looks like a detail query, suppress carousel
                    is_detail_request = True
            
            # UNIT DETAIL VIEW (when user asks for details about a specific unit)
            if is_detail_request and session_memory.last_results:
                # Extract the unit being asked about - Support EN, AR, and Franco patterns
                # Examples: "unit number 123", "unit ra2am 123", "الوحدة رقم 123", "unit #123", "رقم 123"
                unit_id_match = re.search(r'(?:unit|الوحدة|unit ra2am|unit #|رقم)\s*(?:number|رقم)?\s*#?(\d+)', message_lower, re.IGNORECASE)
                if unit_id_match:
                    unit_id_str = unit_id_match.group(1)
                    # Find the unit in last_results
                    unit_data = None
                    for prop in session_memory.last_results:
                        if str(prop.get('unit_id', '')) == unit_id_str:
                            unit_data = prop
                            break
                    
                    if unit_data:
                        unit_id = unit_data.get('unit_id', 'N/A')
                        # Convert video ID to full YouTube URL
                        video_url = unit_data.get('video_url', '')
                        if video_url and not video_url.startswith('http'):
                            video_url = f"https://www.youtube.com/watch?v={video_url}"
                        
                        # Collect ALL available images from the database
                        def add_jpg_if_needed(img_url):
                            """Helper to add .jpg extension if needed"""
                            if img_url and not str(img_url).endswith(('.jpg', '.png', '.jpeg', '.webp')):
                                return img_url + '.jpg'
                            return img_url
                        
                        # Get all image fields
                        unit_image = add_jpg_if_needed(unit_data.get('unit_image', ''))
                        unit_image2 = add_jpg_if_needed(unit_data.get('unit_image2', ''))
                        sm_unit_image = add_jpg_if_needed(unit_data.get('sm_unit_image', ''))
                        compound_image = add_jpg_if_needed(unit_data.get('compound_image', ''))
                        developer_logo = add_jpg_if_needed(unit_data.get('developer_logo', ''))
                        sm_developer_logo = add_jpg_if_needed(unit_data.get('sm_developer_logo', ''))
                        md_developer_logo = add_jpg_if_needed(unit_data.get('md_developer_logo', ''))
                        
                        # Create unit detail structure with ALL images
                        detail_data = {
                            "unit_id": unit_id,
                            "unit_image": unit_image,
                            "unit_image2": unit_image2,
                            "sm_unit_image": sm_unit_image,
                            "compound_image": compound_image,
                            "developer_logo": developer_logo,
                            "sm_developer_logo": sm_developer_logo,
                            "md_developer_logo": md_developer_logo,
                            "image": compound_image or unit_image,  # Fallback for backward compatibility
                            "video_url": video_url,
                            "title": unit_data.get('compound_name', unit_data.get('compound_text', 'N/A')),
                            "property_link": f"https://eshtriaqar.com/en/details/{unit_id}"
                        }
                        
                        # PREPEND unit detail marker and JSON (so it appears at TOP in frontend)
                        response_text = f"###UNIT_DETAIL###{json.dumps(detail_data, default=safe_serialize)}###END_DETAIL###\n\n" + response_text
            
            # Only show carousel for new search results, not for detail follow-ups
            elif getattr(session_memory, 'new_results_fetched', False) and session_memory.last_results and not is_detail_request:
                # Check if result is valid property data (has unit_id)
                first_item = session_memory.last_results[0]
                if isinstance(first_item, dict) and "unit_id" in first_item:
                    # Format data for frontend
                    # Helper function to calculate discounted price
                    def calculate_discount_price(price, promo_text):
                        """Extract discount percentage from promo_text and calculate discounted price."""
                        if not promo_text or not price:
                            return None
                        
                        import re
                        # Try to find discount percentage in promo_text (e.g., "10%", "15% off", "20% discount")
                        discount_match = re.search(r'(\d+)\s*%', str(promo_text))
                        if discount_match:
                            discount_pct = float(discount_match.group(1))
                            original_price = float(price)
                            discounted_price = original_price * (1 - discount_pct / 100)
                            return {
                                "discounted_price": discounted_price,
                                "discount_percentage": discount_pct,
                                "original_price": original_price
                            }
                        return None
                    
                    # Get detected language for localized labels
                    # Get detected language for localized labels
                    detected_lang = str(getattr(session_memory, 'detected_language', 'en')).lower().strip()
                    
                    # Define labels based on language
                    safe_print(f"[DEBUG] Carousel Labels for Language: {detected_lang}")
                    if detected_lang in ['franco', 'franco_arabic', 'franco-arabic']:
                        labels = {
                            "option": "Khiar",
                            "unit_id": "Unit ID", 
                            "area": "Mesa7a",
                            "bedrooms": "Owd", 
                            "bathrooms": "7amam",
                            "price": "Se3r",
                            "delivery": "Tawseel",
                            "status": "7ala",
                            "developer": "Matawer",
                            "model": "Model",
                            "ask_details": "Esa2al 3an el tafaseel",
                            "view_arrow": "→",
                            "found": "La2eet",
                            "properties": "Amaken",
                            "currency": "EGP",
                            "floor": "Dor"
                        }
                    elif detected_lang in ['ar', 'arabic']:
                        labels = {
                            "option": "خيار",
                            "unit_id": "رقم الوحدة",
                            "area": "المساحة",
                            "bedrooms": "غرف",
                            "bathrooms": "حمام",
                            "price": "السعر",
                            "delivery": "التسليم",
                            "status": "الحالة",
                            "developer": "المطور",
                            "model": "الموديل",
                            "ask_details": "اسأل عن التفاصيل",
                            "view_arrow": "←",
                            "found": "لقيتلك",
                            "properties": "وحدات",
                            "currency": "جنيه",
                            "floor": "الدور"
                        }
                    else:  # English
                        labels = {
                            "option": "Option",
                            "unit_id": "Unit ID",
                            "area": "Area",
                            "bedrooms": "Bed",
                            "bathrooms": "Bath",
                            "price": "Price",
                            "delivery": "Delivery",
                            "status": "Status",
                            "developer": "Developer",
                            "model": "Model",
                            "ask_details": "Ask Details",
                            "view_arrow": "→",
                            "found": "Found",
                            "properties": "Properties",
                            "currency": "EGP",
                            "floor": "Floor"
                        }
                    
                    items = []
                    for i, prop in enumerate(session_memory.last_results, 1):
                        title = prop.get('compound_name', prop.get('compound_text', 'N/A'))
                        dev_name = prop.get('developer_name', 'N/A')
                        status = prop.get('status_text', 'Available')
                        
                        # TRANSLATION FOR FRANCO USERS
                        if detected_lang in ['franco', 'franco_arabic', 'franco-arabic']:
                            try:
                                # Translate Arabic fields to Franco/English
                                title = translate_text_logic_func(title, 'ar', 'franco') if re.search(r'[\u0600-\u06FF]', str(title)) else title
                                dev_name = translate_text_logic_func(dev_name, 'ar', 'franco') if re.search(r'[\u0600-\u06FF]', str(dev_name)) else dev_name
                                # Special case for "متاح" (Available)
                                if status == "متاح":
                                    status = "Available"
                                elif re.search(r'[\u0600-\u06FF]', str(status)):
                                    status = translate_text_logic_func(status, 'ar', 'franco')
                            except Exception as e:
                                safe_print(f"Translation error in carousel: {e}")

                        item = {
                            "option": i,
                            "unit_id": prop.get('unit_id', 'N/A'),
                            "code": prop.get('unt_code', 'N/A'),
                            "image": (prop.get('compound_image', '') or prop.get('unit_image', '')) + ('.jpg' if (prop.get('compound_image') or prop.get('unit_image')) and not str(prop.get('compound_image', '') or prop.get('unit_image', '')).endswith(('.jpg', '.png')) else ''),
                            "unit_image": prop.get('unit_image', '') + ('.jpg' if prop.get('unit_image') and not str(prop.get('unit_image', '')).endswith(('.jpg', '.png')) else ''),
                            "compound_image": prop.get('compound_image', '') + ('.jpg' if prop.get('compound_image') and not str(prop.get('compound_image', '')).endswith(('.jpg', '.png')) else ''),
                            "title": title,
                            "price": (f"{float(prop.get('price', 0) or 0):,.0f} جنيه" if detected_lang in ['ar', 'arabic'] else f"{float(prop.get('price', 0) or 0):,.0f} EGP") if prop.get('price') else ("السعر عند الطلب" if detected_lang in ['ar', 'arabic'] else ("Se3r 3and el talab" if detected_lang in ['franco', 'franco_arabic'] else "Price on request")),
                            "has_promo": prop.get('has_promo', 0) == 1,
                            "promo_text": prop.get('promo_text', ''),
                            "discount_info": calculate_discount_price(prop.get('price'), prop.get('promo_text')) if prop.get('has_promo') else None,
                            "area": (f"{prop.get('area', 'N/A')} متر مربع" if detected_lang in ['ar', 'arabic'] else f"{prop.get('area', 'N/A')} m²"),
                            "bedrooms": prop.get('room', 'N/A'),
                            "bathrooms": prop.get('bathroom', 'N/A'),
                            "delivery": prop.get('delivery_date', 'N/A'),
                            "status": status,
                            "developer": dev_name,
                            "floor": prop.get('floor', 'N/A'),
                            "model": prop.get('model_name', 'N/A'),
                            "video_url": f"https://www.youtube.com/watch?v={prop.get('video_url', '')}" if prop.get('video_url') and not prop.get('video_url', '').startswith('http') else prop.get('video_url', '')
                        }
                        items.append(item)

                    carousel_data = {
                        "count": len(session_memory.last_results),
                        "language": detected_lang,  # Add language for frontend
                        "labels": labels,  # Add labels to carousel data
                        "items": items
                    }
                    
                    # REMOVE DUPLICATION: Show carousel ONLY, no LLM text descriptions
                    response_text = ""
                    
                    # PREPEND carousel marker and JSON (so it appears at TOP in frontend)
                    response_text = f"<<PROPERTY_CAROUSEL_DATA>>{json.dumps(carousel_data, default=safe_serialize)}\n\n" + response_text
                    
                    # ADD ALTERNATIVE SEARCH MESSAGE if fuzzy search was used
                    if getattr(session_memory, 'alternative_search', False):
                        original_value = getattr(session_memory, 'original_value', None)
                        fuzzy_field = getattr(session_memory, 'fuzzy_field', 'room')  # Default to room if not set
                        
                        if original_value:
                            # Map field names to user-friendly terms
                            field_names = {
                                'room': {'en': 'bedrooms', 'ar': 'غرف نوم', 'franco': 'bedrooms'},
                                'bathroom': {'en': 'bathrooms', 'ar': 'حمامات', 'franco': 'bathrooms'},
                                'floor': {'en': 'floors', 'ar': 'طوابق', 'franco': 'floors'},
                                'area': {'en': 'm² area', 'ar': 'متر مربع', 'franco': 'm² area'},
                            }
                            
                            # Get user-friendly field name
                            if detected_lang in ['ar', 'arabic']:
                                field_display = field_names.get(fuzzy_field, {}).get('ar', fuzzy_field)
                            elif detected_lang in ['franco', 'franco_arabic', 'franco-arabic']:
                                field_display = field_names.get(fuzzy_field, {}).get('franco', fuzzy_field)
                            else:
                                field_display = field_names.get(fuzzy_field, {}).get('en', fuzzy_field + 's')
                            
                            # Localized alternative messages with dynamic field names
                            if detected_lang in ['ar', 'arabic']:
                                alt_message = f"عذراً، لم أجد وحدات بـ {original_value} {field_display} بالضبط. إليك وحدات بديلة قريبة من طلبك:\n\n"
                            elif detected_lang in ['franco', 'franco_arabic', 'franco-arabic']:
                                alt_message = f"Ana asif, mafeesh units b {original_value} {field_display} belzabt. Dol units 2areeba men el request beta3ak:\n\n"
                            else:  # English
                                alt_message = f"I'm sorry, I couldn't find units with exactly {original_value} {field_display}. Here are alternative units close to your request:\n\n"
                            
                            response_text = alt_message + response_text
                        
                        # Reset the flag after displaying
                        session_memory.alternative_search = False

            # Extract SQL logs if available
            sql_logs = self._extract_sql_logs(session_memory)
            
            # Add response to chat history (CLEANED VERSION to save tokens)
            clean_history_text = response_text
            if "<<PROPERTY_CAROUSEL_DATA>>" in clean_history_text:
                clean_history_text = clean_history_text.split("<<PROPERTY_CAROUSEL_DATA>>")[0].strip()
            if "###UNIT_DETAIL###" in clean_history_text:
                clean_history_text = clean_history_text.split("###UNIT_DETAIL###")[0].strip()
            
            if not clean_history_text:
                clean_history_text = "[Properties found and displayed in carousel]"

            session_memory.chat_history.append({
                "role": "assistant",
                "content": clean_history_text,
                "timestamp": now_ts()
            })
            
            # Log to file (Legacy)
            # self._log_interaction(message, response_text, session_memory)
            
            # ✅ FINAL LOGGING: Capture everything including carousel injection
            total_execution_time = time.time() - start_time
            log_full_action(message, response_text, session_memory, agent_name=actual_agent, execution_time=total_execution_time)
            
            # Reset agent flags for next turn (AFTER logging)
            session_memory.sql_agent_used = False
            session_memory.rag_agent_used = False
            session_memory.chat_agent_used = False

            # Cleanup old sessions
            session_memory.cleanup_old_sessions()
            
            # 🚀 PERFORMANCE: Cache the response for future queries
            result = {
                "response": response_text,
                "detected_language": detected_lang,
                "sql_logs": sql_logs
            }
            
            # Store in cache
            response_cache.set(message, detected_lang, result)
            
            return result
            
        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}"
            safe_print(f"ERROR: Chat error: {e}")
            
            session_memory.chat_history.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": now_ts()
            })
            
            return {
                "response": error_msg,
                "sql_logs": []
            }
    
    def _clean_image_sections(self, text: str) -> str:
        """
        Remove unwanted image sections and markdown from agent responses.
        This ensures no image links or labels appear in the text.
        """
        import re
        
        # Remove "#### Images:" or "## Images:" headers
        text = re.sub(
            r'(?:^|\n)\s*#{1,4}\s*Images?:\s*(?:\n|$)',
            '\n',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # Remove "Images:" section with all its content
        # Matches patterns like:
        # Images:
        # ![Unit Image](url)
        # ![Compound Image](url)
        text = re.sub(
            r'(?:^|\n)\s*Images?:\s*\n(?:\s*!\[.*?\]\(.*?\)\s*\n?)*',
            '',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # Remove patterns like "Unit Image: !View Unit Image" or "Compound Image: !View Compound Image"
        text = re.sub(
            r'(?:^|\n)\s*(?:Unit|Compound|Developer|Property)\s*(?:Image|Logo):\s*!\[?(?:View\s*)?.*?(?:Image|Logo)\]?.*?(?:\n|$)',
            '\n',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # Remove standalone image markdown that might have been missed
        # Matches: ![Unit Image](url) or ![Compound Image](url) or similar
        text = re.sub(
            r'!\[(?:Unit|Compound|Developer|Property)?\s*(?:Image|Logo|Photo).*?\]\(.*?\)',
            '',
            text,
            flags=re.IGNORECASE
        )
        
        # Remove "Unit Image:" and "Compound Image:" labels (with or without URLs)
        # Matches patterns like:
        # Unit Image: https://...
        # Compound Image: https://...
        text = re.sub(
            r'(?:^|\n)\s*(?:Unit|Compound|Developer)\s*(?:Image|Logo):\s*(?:https?://\S+)?\s*',
            '',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # Remove any remaining orphaned "Images:" headers
        text = re.sub(r'(?:^|\n)\s*Images?:\s*(?:\n|$)', '\n', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # ═══════════════════════════════════════════════════════════════
        # VIDEO CONTENT REMOVAL
        # ═══════════════════════════════════════════════════════════════
        
        # Remove "Video Tour:" section with all its content
        # Matches patterns like:
        # Video Tour: https://...
        # Video Tour: [Watch Video](url)
        # Watch Video: url
        text = re.sub(
            r'(?:^|\n)\s*(?:Video\s*Tour|Watch\s*Video):\s*(?:\[.*?\]\(.*?\)|https?://\S+)?\s*',
            '',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # Remove standalone video links (markdown or plain URLs)
        # Matches: [Watch Video](url) or [Video Tour](url)
        text = re.sub(
            r'\[(?:Watch\s*Video|Video\s*Tour|View\s*Video).*?\]\(.*?\)',
            '',
            text,
            flags=re.IGNORECASE
        )
        
        # Remove any standalone video URLs (youtube, vimeo, etc.)
        # This will catch URLs that might be displayed as plain text
        text = re.sub(
            r'(?:^|\n|\s)(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com|dailymotion\.com)/\S+',
            '',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # Remove any text mentioning "video tour" or "watch video" followed by any content
        text = re.sub(
            r'(?:^|\n)\s*(?:video\s*tour|watch\s*video).*?(?:\n|$)',
            '\n',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        # Clean up excessive newlines (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # ═══════════════════════════════════════════════════════════════
        # REMOVE DEBUG MARKERS AND JSON DATA
        # ═══════════════════════════════════════════════════════════════
        
        # 1. Remove ###UNIT_DETAIL###...###END_DETAIL###
        text = re.sub(
            r'###UNIT_DETAIL###.*?###END_DETAIL###',
            '',
            text,
            flags=re.DOTALL
        )

        # 2. Remove <<PROPERTY_CAROUSEL_DATA>> and trailing content
        text = re.sub(
            r'<<PROPERTY_CAROUSEL_DATA>>.*$',
            '',
            text,
            flags=re.DOTALL | re.MULTILINE
        )

        # 3. Remove <<PAYMENT_PLAN_DATA>> and trailing content
        text = re.sub(
            r'<<PAYMENT_PLAN_DATA>>.*$',
            '',
            text,
            flags=re.DOTALL | re.MULTILINE
        )

        # 4. Remove leftover JSON arrays (if any)
        text = re.sub(
            r'\[\s*{\s*"unit_id".*?\}\s*\]',
            '',
            text,
            flags=re.DOTALL
        )
        
        text = re.sub(
            r'\[\s*\{\s*".*?".*?\}\s*\]',
            '',
            text,
            flags=re.DOTALL
        )

        # Clean up leading/trailing whitespace
        text = text.strip()
        
        return text

    
    def _extract_sql_logs(self, session_memory: SessionMemory) -> List[Dict[str, Any]]:
        """Extract SQL logs from session memory."""
        logs = []
        
        if session_memory.last_sql:
            log_entry = {
                "query_name": "Property Search",
                "sql": session_memory.last_sql,
                "success": bool(session_memory.last_results),
                "row_count": len(session_memory.last_results) if session_memory.last_results else 0,
                "error": None
            }
            
            # Check for errors in results
            if session_memory.last_results and isinstance(session_memory.last_results, list):
                if len(session_memory.last_results) > 0 and "error" in session_memory.last_results[0]:
                    log_entry["success"] = False
                    log_entry["error"] = session_memory.last_results[0]["error"]
            
            logs.append(log_entry)
        
        return logs
    
    def _log_interaction(self, user_query: str, bot_reply: str, session_memory: SessionMemory):
        """Log interaction to file."""
        timestamp = now_ts()
        
        try:
            with open(settings.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}]\n")
                f.write(f"User: {user_query}\n")
                
                if session_memory.safety_check:
                    f.write(f"Safety Check: {session_memory.safety_check}\n")
                
                if session_memory.last_sql:
                    f.write(f"SQL: {session_memory.last_sql}\n")
                
                if session_memory.last_eval:
                    f.write(f"SQL Evaluator: {session_memory.last_eval}\n")
                
                if session_memory.last_rag_results:
                    f.write(f"RAG Results: {session_memory.last_rag_results[:200]}...\n")
                
                if session_memory.last_rag_eval:
                    f.write(f"RAG Evaluator: {session_memory.last_rag_eval}\n")
                
                f.write(f"Bot: {bot_reply}\n")
                f.write("=" * 60 + "\n\n")
        except Exception as e:
            safe_print(f"WARNING: Failed to log interaction: {e}")
    
    def clear_session(self, session_id: str):
        """Clear session memory."""
        if session_id in self.sessions:
            self.sessions[session_id].reset()


# Global chat service instance
chat_service = ChatService()
