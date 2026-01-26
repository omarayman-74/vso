
"""Language detection and translation service using LLM-based analysis."""
import re
import json
import os
from langchain.tools import tool
# from langchain_openai import ChatOpenAI
from config import settings

# Global LLM instance (lazy loaded)
_llm_instance = None

def _get_llm():
    """Get or initialize the LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        from langchain_openai import ChatOpenAI
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        _llm_instance = ChatOpenAI(model=settings.llm_model, temperature=0.2)
    return _llm_instance

# Session memory structure reference (handled by Agent logic, not stored here globally)
# But we keep the logic structure.

# ═══════════════════════════════════════════════════════════════════════════
# 1. LANGUAGE DETECTION TOOL
# ═══════════════════════════════════════════════════════════════════════════

@tool
def enhanced_detect_language_tool(text: str) -> str:
    """
    Enhanced language detection with real estate context awareness.
    CRITICAL: Distinguish between Arabic with numbers vs Franco-Arabic.
    """
    return detect_language_logic(text)

def detect_language_logic(text: str) -> str:
    """
    Enhanced language detection with real estate context awareness.
    CRITICAL: Distinguish between Arabic with numbers vs Franco-Arabic.
    """
    if not text or not text.strip():
        return json.dumps({"language": "en", "confidence": 0.0, "reasoning": "Empty input"})
    
    # ✅ EXTRACT LANGUAGE HINT if present (highest priority)
    # Pattern: [Respond in English|Arabic|Franco-Arabic]
    hint_pattern = r'\[Respond in (English|Arabic|Franco-Arabic)\]'
    hint_match = re.search(hint_pattern, text, re.IGNORECASE)
    
    if hint_match:
        hint_lang = hint_match.group(1).lower()
        # Map to our language codes
        lang_map = {
            'english': 'en',
            'arabic': 'ar', 
            'franco-arabic': 'franco'
        }
        detected_lang = lang_map.get(hint_lang, 'en')
        
        # Remove hint from text for further processing
        clean_text = re.sub(hint_pattern, '', text, flags=re.IGNORECASE).strip()
        
        return json.dumps({
            "language": detected_lang,
            "confidence": 1.0,
            "reasoning": f"Explicit language hint detected: [{hint_lang}]",
            "detected_patterns": ["language_hint"],
            "arabic_ratio": 0.0,
            "hint_provided": True
        })
        
    # ✅ QUICK FRANCO CHECK: Common Franco words that should trigger immediate Franco detection
    text_lower = text.lower()
    strong_franco_indicators = [
        'meen', 'ezay', 'eh', 'ezzay', 'fe', 'aywa', 'la2', 'keda', 'hena',
        '3ayez', '3ayz', 'ana', 'enta', 'bey3', 'bey2', 'el-', 'm3ad', 'yalla',
        'sha2a', '2od', 'owd', '7amam', 'ghorfa', '7aga', 'kebira', 'so3ayara',
        'tafaseel', 'aktr', 'esa2al', 'wareny', 'nezam', 'sadad', 'ra2am'
    ]

    # Use word boundary matching to avoid false positives (e.g., "shareholders" should NOT match "eh")
    franco_matches = []
    for word in strong_franco_indicators:
        # Match whole words with word boundaries
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_lower):
            franco_matches.append(word)

    if franco_matches and len(text_lower) < 100:  # Short queries with Franco words
        # print(f"[QUICK FRANCO DETECTION] Found: {franco_matches}")
        return json.dumps({
            "language": "franco",
            "confidence": 0.95,
            "reasoning": f"Quick detection: Found Franco indicators: {franco_matches}",
            "detected_patterns": franco_matches,
            "arabic_ratio": 0.0
        })

    # 🚀 PERFORMANCE: Skip LLM language detection when disabled
    if not settings.use_llm_language_detection:
        # Count Arabic characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        alpha_chars = sum(1 for c in text if c.isalpha() or '\u0600' <= c <= '\u06FF')
        arabic_ratio = arabic_chars / alpha_chars if alpha_chars > 0 else 0

        franco_patterns = [
            'meen', 'ezay', 'ezzay', '3ayez', '2ana', '7aga', 'sha2a',
            '2od', '7amam', 'ghorfa', 'fe ', ' el-', 'bey3', 'bey2',
            'kebira', 'so3ayara', 'ta2riban', '3ala', 'm3ad', 'yalla'
        ]
        franco_matches = [p for p in franco_patterns if p in text_lower]

        if arabic_ratio > 0.5:
            return json.dumps({
                "language": "ar",
                "confidence": 0.9,
                "reasoning": f"Fast heuristic: High Arabic ratio ({arabic_ratio:.1%})",
                "detected_patterns": [],
                "arabic_ratio": arabic_ratio
            })
        if franco_matches:
            return json.dumps({
                "language": "franco",
                "confidence": 0.85,
                "reasoning": f"Fast heuristic: Franco patterns: {franco_matches}",
                "detected_patterns": franco_matches,
                "arabic_ratio": arabic_ratio
            })

        return json.dumps({
            "language": "en",
            "confidence": 0.6,
            "reasoning": "Fast heuristic: Default to English",
            "detected_patterns": [],
            "arabic_ratio": arabic_ratio
        })


    prompt = f"""You are an expert language detection system specialized in real estate queries.

Analyze this text: "{text}"

**CRITICAL RULES FOR ARABIC vs FRANCO DETECTION**:

1. **Standalone Numbers Are NOT Language Indicators**:
   - "3 غرف" → The "3" is just a quantity, NOT Franco
   - These are ARABIC with numbers, NOT Franco-Arabic

2. **Franco-Arabic Uses Numbers AS LETTERS INSIDE WORDS**:
   - "3ayez" (عايز) → "3" replaces ع
   - "sha2a" (شقة) → "2" replaces ق
   - Numbers are PART of the word, not separate

3. **Common Franco Words** (instant Franco detection):
   - meen, ezay, ezzay, 3ayez, sha2a, 2od, 7amam, el-, bey3, m3ad
   - If text contains ANY of these → FRANCO

4. **Primary Script Determines Language**:
   - Arabic ratio > 50% → ARABIC
   - Latin letters with Franco patterns → FRANCO
   - Only English words → ENGLISH

**Real Estate Franco Patterns**:
meen, ezay, 3ayez, sha2a, 2od, 7amam, ghorfa, fe, el-, bey3rfo, m3ad, yalla, keda, hena

Return ONLY JSON:
{{"language": "en"/"ar"/"franco", "confidence": 0.0-1.0, "reasoning": "explanation", "detected_patterns": ["list"], "arabic_ratio": 0.0-1.0}}
"""

    try:
        response = _get_llm().invoke(prompt)
        result = response.content.strip()
        result = result.replace("```json", "").replace("```", "").strip()
        detection = json.loads(result)

        detection.setdefault("language", "en")
        detection.setdefault("confidence", 0.5)
        detection.setdefault("reasoning", "Default detection")
        detection.setdefault("detected_patterns", [])
        detection.setdefault("arabic_ratio", 0.0)

        # Normalize keys to match old system for compatibility if needed, OR we stick to new keys
        # We will use NEW KEYS: 'ar', 'franco', 'en'
        return json.dumps(detection)

    except Exception as e:
        # Enhanced fallback
        text_lower = text.lower()

        # Count Arabic characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        alpha_chars = sum(1 for c in text if c.isalpha() or '\u0600' <= c <= '\u06FF')
        arabic_ratio = arabic_chars / alpha_chars if alpha_chars > 0 else 0

        # Franco patterns (expanded)
        franco_patterns = [
            'meen', 'ezay', 'ezzay', '3ayez', '2ana', '7aga', 'sha2a',
            '2od', '7amam', 'ghorfa', 'fe ', ' el-', 'bey3', 'bey2',
            'kebira', 'so3ayara', 'ta2riban', '3ala', 'm3ad', 'yalla'
        ]
        franco_matches = [p for p in franco_patterns if p in text_lower]

        # Decision logic
        if arabic_ratio > 0.5:
            fallback = {
                "language": "ar",
                "confidence": 0.9,
                "reasoning": f"Fallback: High Arabic ratio ({arabic_ratio:.1%})",
                "detected_patterns": [],
                "arabic_ratio": arabic_ratio
            }
        elif franco_matches:  # ANY Franco match = Franco
            fallback = {
                "language": "franco",
                "confidence": 0.85,
                "reasoning": f"Fallback: Franco patterns: {franco_matches}",
                "detected_patterns": franco_matches,
                "arabic_ratio": arabic_ratio
            }
        else:
            fallback = {
                "language": "en",
                "confidence": 0.6,
                "reasoning": "Fallback: Default to English",
                "detected_patterns": [],
                "arabic_ratio": arabic_ratio
            }

        return json.dumps(fallback)



def get_language_instruction(language: str) -> str:
    """
    Get instruction text for agent on how to respond in the detected language.
    
    Args:
        language: Detected language ("en", "ar", "franco")
        
    Returns:
        Instruction string for the agent
    """
    instructions = {
        "english": "Respond ONLY in English. Use professional, business-appropriate language.",
        "en": "Respond ONLY in English. Use professional, business-appropriate language.",
        
        "arabic": """الرد باللغة العربية المصرية فقط. استخدم اللهجة المصرية الرسمية.
(Respond ONLY in Egyptian Arabic script. Use formal Egyptian dialect, not Gulf, Levantine, or Maghrebi dialects.
Focus on Egyptian real estate terminology and expressions.)

**Important**: When providing property details, use the ACTUAL data from the database. Don't use placeholders. Fill in all available information about the property including:
- Area (المساحة), bedrooms (الغرف), bathrooms (الحمامات), floor (الدور)
- Delivery date (موعد التسليم), status (الحالة)
- Price details (السعر), down payment (المقدم), installment plans (نظام التقسيط)
- Any available discounts or promotional offers (العروض والخصومات)

If information is not available in the database, say "غير محدد" (not specified) instead of using placeholder brackets.""",


        "ar": """الرد باللغة العربية المصرية فقط. استخدم اللهجة المصرية الرسمية.
(Respond ONLY in Egyptian Arabic script. Use formal Egyptian dialect, not Gulf, Levantine, or Maghrebi dialects.
Focus on Egyptian real estate terminology and expressions.)

**Important**: When providing property details, use the ACTUAL data from the database. Don't use placeholders. Fill in all available information about the property including:
- Area (المساحة), bedrooms (الغرف), bathrooms (الحمامات), floor (الدور)
- Delivery date (موعد التسليم), status (الحالة)
- Price details (السعر), down payment (المقدم), installment plans (نظام التقسيط)
- Any available discounts or promotional offers (العروض والخصومات)

If information is not available in the database, say "غير محدد" (not specified) instead of using placeholder brackets.""",


        "franco_arabic": """Respond ONLY in Egyptian Franco-Arabic (Arabizi). You MUST write Egyptian Arabic using Latin letters and numbers.

CRITICAL RULES FOR EGYPTIAN FRANCO-ARABIC:
- Use numbers for Arabic letters: 3 for ع, 7 for ح, 2 for ء, 5 for خ, 8 for ق/غ, 9 for ص
- Write in FORMAL Egyptian dialect (NOT Gulf, Levantine, or Lebanese)
- Use PROFESSIONAL, business-appropriate tone for real estate

**Search Result Format**:
La2eet [number] [type] fe [area]:
1. **[Project]**: [area]m2 | [rooms] Owd | [bathrooms] 7amam | [price] EGP

**Property Detail Format (Mandatory for single unit info)**:
# 🏢 [Project] - Unit ra2am [ID]

## 📝 Wasf el Unit:
[Detailed description of features and amenities in Franco]

## 📊 Mowasafat:
- **Mesa7a**: [area] m2
- **Owd**: [rooms]
- **7amam**: [bathrooms]
- **Floor**: [floor]
- **Delivery**: [date]
- **Status**: [status]

## 💰 Se3r wa Nezam el Sadad:
- **Se3r**: [price] EGP
- **Mo2adem**: [down payment]
- **Nezam el Sadad**: [details]

## 🏗️ Developer info:
[Developer Name] - [Short info]

Law m7tag t3raf ay 7aga tanya, 2oly!""",
        
        "franco": """Respond ONLY in Egyptian Franco-Arabic (Arabizi). You MUST write Egyptian Arabic using Latin letters and numbers.

CRITICAL RULES FOR EGYPTIAN FRANCO-ARABIC:
- Use numbers for Arabic letters: 3 for ع, 7 for ح, 2 for ء, 5 for خ, 8 for ق/غ, 9 for ص
- Write in FORMAL Egyptian dialect (NOT Gulf, Levantine, or Lebanese)
- Use PROFESSIONAL, business-appropriate tone for real estate

**Search Result Format**:
La2eet [number] [type] fe [area]:
1. **[Project]**: [area]m2 | [rooms] Owd | [bathrooms] 7amam | [price] EGP

**Property Detail Format (Mandatory for single unit info)**:
# 🏢 [Project] - Unit ra2am [ID]

## 📝 Wasf el Unit:
[Detailed description of features and amenities in Franco]

## 📊 Mowasafat:
- **Mesa7a**: [area] m2
- **Owd**: [rooms]
- **7amam**: [bathrooms]
- **Floor**: [floor]
- **Delivery**: [date]
- **Status**: [status]

## 💰 Se3r wa Nezam el Sadad:
- **Se3r**: [price] EGP
- **Mo2adem**: [down payment]
- **Nezam el Sadad**: [details]

## 🏗️ Developer info:
[Developer Name] - [Short info]

Law m7tag t3raf ay 7aga tanya, 2oly!"""
    }
    
    return instructions.get(language, instructions["english"])


# ═══════════════════════════════════════════════════════════════════════════
# 2. RESPONSE LANGUAGE PREFERENCE DETECTOR

# ═══════════════════════════════════════════════════════════════════════════

@tool
def detect_response_language_preference(user_query: str, detected_query_language: str) -> str:
    """
    Detect if user explicitly requested response in a different language.

    Examples:
    - "3ayez sha2a jaweb b english" → wants English response
    - "Show me properties in Arabic" → wants Arabic response
    - "أريد شقة جاوب بالفرانكو" → wants Franco response
    - "عايز شقة" → no preference (respond in same language)
    """

    # Quick regex patterns for common phrases
    patterns = {
        'en': [
            r'\b(in english|respond in english|answer in english|reply in english)\b',
            r'\b(جاوب ب ?english|رد ب ?english)\b'
        ],
        'ar': [
            r'\b(in arabic|respond in arabic|answer in arabic|بالعربي|بالعربى)\b',
            r'\b(جاوب بالعربي|رد بالعربي)\b'
        ],
        'franco': [
            r'\b(in franco|بالفرانكو|b franco|fe franco)\b',
            r'\b(جاوب بالفرانكو|jaweb b franco)\b'
        ]
    }

    query_lower = user_query.lower()

    # Check patterns
    for lang, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return json.dumps({
                    "has_preference": True,
                    "preferred_language": lang,
                    "detected_from": "explicit_request"
                })

    # If no explicit preference found, ask LLM (simple check)
    prompt = f"""Does this user query contain an explicit request for the response language?

Query: "{user_query}"
Query Language: {detected_query_language}

Look for phrases like:
- "answer in English/Arabic/Franco"
- "respond in..."
- "جاوب بالعربي / بالفرانكو"
- "jaweb b english"

Return ONLY JSON:
{{
    "has_preference": true/false,
    "preferred_language": "en"/"ar"/"franco" (or null),
    "confidence": 0.0-1.0
}}
"""

    try:
        result = _get_llm().invoke(prompt).content.strip()
        result = result.replace("```json", "").replace("```", "").strip()

        data = json.loads(result)

        # If LLM found preference, use it
        if data.get("has_preference") and data.get("confidence", 0) > 0.7:
            return json.dumps({
                "has_preference": True,
                "preferred_language": data["preferred_language"],
                "detected_from": "llm_analysis"
            })

    except Exception as e:
        # print(f"[WARNING] Language preference detection failed: {e}")
        pass

    # Default: no preference, respond in same language
    return json.dumps({
        "has_preference": False,
        "preferred_language": detected_query_language,
        "detected_from": "default"
    })


# ═══════════════════════════════════════════════════════════════════════════
# 3. TRANSLATION TOOL (Franco/Arabic/English)
# ═══════════════════════════════════════════════════════════════════════════

@tool
def enhanced_translate_text_tool(text: str, source_lang: str, target_lang: str) -> str:
    """Enhanced translation - Franco/Arabic/English ONLY. NO FRENCH ALLOWED."""
    return translate_text_logic(text, source_lang, target_lang)

def translate_text_logic(text: str, source_lang: str, target_lang: str) -> str:
    """Enhanced translation - Franco/Arabic/English ONLY. NO FRENCH ALLOWED."""

    if source_lang == target_lang:
        return text

    # ✅ CRITICAL: Validate target language
    if target_lang not in ['franco', 'ar', 'en']:
        # print(f"[ERROR] Invalid target language: {target_lang}")
        return text

    # ✅ SPECIAL HANDLING: Arabic → Franco (this is where French creeps in!)
    if source_lang == 'ar' and target_lang == 'franco':

        prompt = f"""Translate Arabic to NATURAL Franco-Arabic (the way Egyptians ACTUALLY write online).

**CRITICAL**: Write how people TEXT on WhatsApp/Facebook, NOT formal transliteration!

**CRITICAL INSTRUCTIONS**:
- Franco-Arabic uses LATIN LETTERS + NUMBERS to write Arabic words
- Numbers represent Arabic letters:
  2 = ء
  3 = ع
  4 = ش
  5 = خ
  7 = ح
  8 = غ

- Use ONLY Latin alphabet (a-z) + numbers (0-9)
- **NEVER USE FRENCH WORDS** like "voici", "propriété", "chambre", "superficie"
- Keep standalone numbers as-is (3 rooms = 3 owd, NOT 3 chambres)

**Franco-Arabic Real Estate Vocabulary**:
Arabic → Franco (CORRECT):
- عايز → 3ayez
- شقة → sha2a / apartment
- غرفة/أوضة → ghorfa / 2oda / owd
- حمام → 7amam / bathroom
- مساحة → mesa7a / area
- سعر → se3r / price
- موقع → maw2e3 / location
- مطور → matawer / developer
- حالة → 7ala / status
- مؤقتاً → mo2akatan / temporarily
- مقفول → ma2foul / locked

**WRONG (French - NEVER use these)**:
- ❌ propriété (use: sha2a / property)
- ❌ voici (use: hena / here)
- ❌ chambre (use: owd / ghorfa / room)
- ❌ superficie (use: mesa7a / area)
- ❌ prix (use: se3r / price)
- ❌ emplacement (use: makan / location)
- ❌ développeur (use: developer / matawer)

**Format for Property Listings**:
```
La2eet 5 sha2a b 3 owd:

1. Property ID: [number]
   - Mesa7a: [number] m²
   - Se3r: [number] EGP
   - Owd: [number] | 7amam: [number]
   - Makan: [location]
   - Developer: [name]
   - Status: [status]
```

**Input Text (Arabic)**:
{text}

**Your Task**:
Translate to Franco-Arabic using ONLY Latin letters and numbers.
Keep property data (IDs, prices, numbers) unchanged.
Use the vocabulary above.

**CRITICAL**: If you use ANY French words, you FAILED the task.

Return ONLY the Franco-Arabic translation:
"""

    # ✅ For other translation directions
    else:
        prompt = f"""You are a real estate translator.

**SUPPORTED LANGUAGES**: Franco-Arabic, Arabic, English ONLY
**STRICTLY FORBIDDEN**: French language in any form

Translation Direction: {source_lang} -> {target_lang}

**Input Text**:
{text}

**Franco-Arabic Rules** (if target is Franco):
- Use Latin alphabet + numbers for Arabic sounds
- 3ayez = عايز (want)
- sha2a = شقة (apartment)
- 2od/owd = أوضة (room)
- 7amam = حمام (bathroom)
- Keep numbers as digits (3, 5, 100)
- NEVER use French words

**Translation Rules**:
1. Preserve all numbers and IDs
2. Keep property terminology accurate
3. Maintain formatting (bullet points, line breaks)
4. Don't add or remove information

Return ONLY the translated text (no explanations):
"""

    try:
        response = _get_llm().invoke(prompt)
        translated = response.content.strip()

        # ✅ ENHANCED VALIDATION: Check for French words
        french_words = [
            'propriété', 'voici', 'chambre', 'superficie', 'prix',
            'emplacement', 'développeur', 'salle de bain', 'statut',
            'temporairement', 'verrouillé', 'metre', 'egyptien'
        ]

        french_detected = [fw for fw in french_words if fw.lower() in translated.lower()]

        if french_detected:
            # print(f"[ERROR] French words detected in translation: {french_detected}")
            # print(f"[ERROR] Attempting auto-correction...")

            # Auto-correct French to Franco
            replacements = {
                'propriété': 'property',
                'voici': 'hena',
                'chambre': 'owd',
                'superficie': 'mesa7a',
                'prix': 'se3r',
                'emplacement': 'makan',
                'développeur': 'developer',
                'salle de bain': '7amam',
                'statut': 'status',
                'temporairement': 'mo2akatan',
                'verrouillé': 'ma2foul',
                'metre': 'm',
                'egyptien': 'EGP'
            }

            for french, franco in replacements.items():
                translated = re.sub(french, franco, translated, flags=re.IGNORECASE)

            # print(f"[INFO] Auto-correction applied")

        return translated

    except Exception as e:
        print(f"[ERROR] Translation failed: {e}")
        return text

# Map legacy function to LOGIC function (callable)
detect_language = detect_language_logic
# Map explicit translation logic for import
translate_text_logic_func = translate_text_logic

# Legacy adaptation
# detect_language = enhanced_detect_language_tool
