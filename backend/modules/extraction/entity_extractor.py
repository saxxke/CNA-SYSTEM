import re
import spacy

_nlp = None
_nlp_loaded = False

def get_nlp():
    global _nlp, _nlp_loaded
    if not _nlp_loaded:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            _nlp = None
        _nlp_loaded = True
    return _nlp

def __getattr__(name: str):
    if name == "nlp":
        return get_nlp()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def extract_entities(text: str) -> list:
    """
    Combines spaCy NER and structured regex/rule extraction.
    Returns a list of dictionaries with extracted entities.
    """
    if not text:
        return []
        
    extracted = []
    
    # 1. SPACY NER
    nlp = get_nlp()
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            mapped_type = None
            if ent.label_ == "PERSON":
                mapped_type = "PERSON"
            elif ent.label_ in ["ORG", "ORGANIZATION"]:
                mapped_type = "ORGANIZATION"
            elif ent.label_ in ["GPE", "LOC", "FAC"]:
                mapped_type = "LOCATION"
            elif ent.label_ == "DATE":
                mapped_type = "DATE"
            elif ent.label_ == "MONEY":
                mapped_type = "MONEY"
                
            if mapped_type:
                extracted.append({
                    "type": mapped_type,
                    "value": ent.text.strip(),
                    # SpaCy en_core_web_sm doesn't natively expose entity confidence easily,
                    # so we document 0.85 as a static probability for ML predictions in this MVP.
                    "confidence": 0.85,
                    "evidence": ent.text,
                    "source": "SPACY_NER"
                })

    # 2. STRUCTURED EXTRACTION (regex)
    
    # PHONE: +91 9000000004 or 9000000004 or 90000-00004
    # Our synthetic data uses phones starting with 9
    phone_pattern = r'(?:\+91\s*)?9\d{4}[-\s]?\d{5}'
    for match in re.finditer(phone_pattern, text):
        extracted.append({
            "type": "PHONE",
            "value": match.group().strip(),
            "confidence": 1.0,
            "evidence": match.group(),
            "source": "RULE"
        })
        
    # BANK_ACCOUNT: Usually 10 digits in our synthetic dataset. Variation: 1234 567890
    bank_pattern = r'\b\d{4}\s?\d{6}\b'
    for match in re.finditer(bank_pattern, text):
        val = match.group().strip()
        # prevent overlap with phones that don't have spaces or dashes
        if not re.match(phone_pattern, val):
            extracted.append({
                "type": "BANK_ACCOUNT",
                "value": val,
                "confidence": 1.0,
                "evidence": match.group(),
                "source": "RULE"
            })

    # VEHICLE: WB00XX0001 or WB-00-XX-0001
    vehicle_pattern = r'\b[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{1,2}[-\s]?\d{4}\b'
    for match in re.finditer(vehicle_pattern, text):
        extracted.append({
            "type": "VEHICLE",
            "value": match.group().strip(),
            "confidence": 1.0,
            "evidence": match.group(),
            "source": "RULE"
        })
        
    # CASE_ID: CASE-001
    case_pattern = r'\bCASE-\d{3}\b'
    for match in re.finditer(case_pattern, text):
        extracted.append({
            "type": "CASE_ID",
            "value": match.group().strip(),
            "confidence": 1.0,
            "evidence": match.group(),
            "source": "RULE"
        })
        
    # MONEY: $1000, Rs 500, ₹5000, 5000 INR
    money_pattern = r'(?:₹|\$|Rs\.?)\s?\d+(?:,\d+)*(?:\.\d{2})?|\b\d+(?:,\d+)*(?:\.\d{2})?\s*INR\b'
    for match in re.finditer(money_pattern, text):
        extracted.append({
            "type": "MONEY",
            "value": match.group().strip(),
            "confidence": 1.0,
            "evidence": match.group(),
            "source": "RULE"
        })
        
    # DATE: 2024-01-01
    date_pattern = r'\b\d{4}-\d{2}-\d{2}\b'
    for match in re.finditer(date_pattern, text):
        extracted.append({
            "type": "DATE",
            "value": match.group().strip(),
            "confidence": 1.0,
            "evidence": match.group(),
            "source": "RULE"
        })
        
    # 4. DUPLICATE HANDLING
    # Merge exact overlaps prioritizing RULE
    unique_entities = {}
    for ent in extracted:
        key = ent["evidence"].strip().lower()
        
        if key in unique_entities:
            existing = unique_entities[key]
            # Prioritize RULE over SPACY_NER if there's a conflict
            if existing["source"] == "SPACY_NER" and ent["source"] == "RULE":
                unique_entities[key] = ent
            # If same source, keep the first one
        else:
            unique_entities[key] = ent
            
    # Substring duplicate removal (e.g. spacy finds "the $500" and rule finds "$500")
    # For now, relying on exact matching as per rules.
            
    return list(unique_entities.values())
