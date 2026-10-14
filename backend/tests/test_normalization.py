import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.entity_resolution.normalization import normalize_entity

def test_phone_normalization():
    # "+91 9000000004", "9000000004", "90000-00004"
    res1 = normalize_entity("PHONE", "+91 9000000004")
    res2 = normalize_entity("PHONE", "9000000004")
    res3 = normalize_entity("PHONE", "90000-00004")
    
    assert res1["canonical_value"] == "9000000004"
    assert res2["canonical_value"] == "9000000004"
    assert res3["canonical_value"] == "9000000004"
    assert res1["canonical_value"] == res2["canonical_value"] == res3["canonical_value"]

def test_bank_account_normalization():
    res1 = normalize_entity("BANK_ACCOUNT", "BA-00012345")
    res2 = normalize_entity("BANK_ACCOUNT", "BA00012345")
    res3 = normalize_entity("BANK_ACCOUNT", "ba 00012345")
    
    assert res1["canonical_value"] == "BA00012345"
    assert res1["canonical_value"] == res2["canonical_value"]
    assert res1["canonical_value"] == res3["canonical_value"]

def test_vehicle_normalization():
    res1 = normalize_entity("VEHICLE", "WB00XX0001")
    res2 = normalize_entity("VEHICLE", "WB-00-XX-0001")
    res3 = normalize_entity("VEHICLE", "wb 00 xx 0001")
    
    assert res1["canonical_value"] == "WB00XX0001"
    assert res1["canonical_value"] == res2["canonical_value"]
    assert res1["canonical_value"] == res3["canonical_value"]

def test_person_normalization():
    # Arjun Sen, Arjun K. Sen, A. Sen
    res1 = normalize_entity("PERSON", "Arjun Sen")
    res2 = normalize_entity("PERSON", "Arjun K. Sen")
    res3 = normalize_entity("PERSON", "A. Sen")
    res4 = normalize_entity("PERSON", "  Arjun   Sen  ")
    
    assert res1["canonical_value"] == "arjun sen"
    assert res1["canonical_value"] == res4["canonical_value"] # whitespace norm
    
    # Must NOT declare them the same
    assert res1["canonical_value"] != res2["canonical_value"]
    assert res2["canonical_value"] == "arjun k sen" # punctuated removed and spaced
    assert res3["canonical_value"] == "a sen"
    
def test_location_normalization():
    res1 = normalize_entity("LOCATION", "New Delhi")
    res2 = normalize_entity("LOCATION", "new delhi")
    res3 = normalize_entity("LOCATION", "New  Delhi.")
    
    assert res1["canonical_value"] == "new delhi"
    assert res1["canonical_value"] == res2["canonical_value"]
    assert res1["canonical_value"] == res3["canonical_value"]

def test_organization_normalization():
    res1 = normalize_entity("ORGANIZATION", "Global-Tech Solutions")
    res2 = normalize_entity("ORGANIZATION", "Global Tech Solutions")
    
    assert res1["canonical_value"] == "global tech solutions"
    assert res1["canonical_value"] == res2["canonical_value"]

def test_preservation_of_original_value():
    res = normalize_entity("PERSON", "Arjun Sen")
    assert res["original_value"] == "Arjun Sen"
    assert res["entity_type"] == "PERSON"

def test_empty_handling():
    res = normalize_entity("PHONE", "")
    assert res["canonical_value"] == ""
    assert res["original_value"] == ""
