import re

def normalize_entity(entity_type: str, value: str) -> dict:
    """
    Converts different representations of the same structured entity into a 
    canonical representation. This is deterministic normalization, NOT entity resolution.
    """
    if not value:
        return {
            "entity_type": entity_type,
            "original_value": value,
            "canonical_value": ""
        }
        
    original_value = value
    canonical_value = value
    
    if entity_type == "PHONE":
        # Remove spaces, hyphens, parentheses.
        canonical_value = re.sub(r'[\s\-\(\)]', '', canonical_value)
        # Strip +91 country code prefix to allow consistent 10-digit matching
        if canonical_value.startswith('+91') and len(canonical_value) == 13:
            canonical_value = canonical_value[3:]
    
    elif entity_type == "BANK_ACCOUNT":
        # Remove unnecessary formatting characters like spaces and hyphens. Uppercase.
        canonical_value = re.sub(r'[\s\-]', '', canonical_value).upper()
        
    elif entity_type == "VEHICLE":
        # Remove spaces, hyphens, punctuation. Uppercase.
        canonical_value = re.sub(r'[\s\-\.,]', '', canonical_value).upper()
        
    elif entity_type in ["PERSON", "LOCATION", "ORGANIZATION"]:
        # Conservative normalization:
        # Lowercase, normalize repeated spaces, maybe remove basic punctuation
        canonical_value = canonical_value.lower()
        # Punctuation normalization: remove common non-essential punctuation but we must be careful.
        # Let's remove periods and commas for basic name/org normalization.
        # Or just standard strip and space normalization. 
        # The prompt says: "punctuation normalization". Let's remove basic punctuation (, . -) 
        # but keep alphanumeric.
        canonical_value = re.sub(r'[,\.\-]', ' ', canonical_value)
        # normalize whitespace
        canonical_value = re.sub(r'\s+', ' ', canonical_value).strip()
        
    else:
        # Default fallback for unhandled types like CASE_ID, MONEY, DATE
        canonical_value = canonical_value.strip()

    return {
        "entity_type": entity_type,
        "original_value": original_value,
        "canonical_value": canonical_value
    }
