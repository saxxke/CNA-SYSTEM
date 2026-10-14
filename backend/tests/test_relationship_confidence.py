import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.ml.relationship_confidence import extract_features, train_model, predict_confidence, MODEL_PATH, DatasetContext
import joblib

def test_feature_extraction():
    rel = {
        "source": "PERSON-017",
        "target": "PERSON-043",
        "relationship_type": "CONTACTED",
        "evidence": "PERSON-017 contacted PERSON-043 using PHONE-004.",
        "case_id": "CASE-001",
        "detection_method": "RULE"
    }
    feats = extract_features(rel)
    assert len(feats) == 7
    # Text evidence strength: ~48 chars / 100 = 0.48
    assert 0.0 < feats[1] <= 1.0
    # Keyword match
    assert feats[2] == 1.0
    # Cross-case connectivity (at least 1 from CASE-001)
    assert feats[6] >= 1.0
    # Entity similarity is not ID based. Should just run without error and be a float
    assert isinstance(feats[0], float)

def test_supporting_and_source_record_counts():
    # If we pass actual dataset IDs, we should see counts > 0
    rel = {
        "source": "PERSON-017",
        "target": "PERSON-043",
        "relationship_type": "CONTACTED",
        "evidence": "PERSON-017 contacted PERSON-043 using PHONE-004.",
    }
    feats = extract_features(rel)
    
    # Feature 3 is supp_count, 4 is src_count
    # Since PERSON-017 is in communications, they should be > 0.0
    # If the tests are run without dataset, they default to 1.0
    assert feats[3] > 0.0
    assert feats[4] > 0.0
    
def test_relationship_frequency_evidence_derived():
    # Feature 5 is rel_freq
    rel_contacted = {"relationship_type": "CONTACTED"}
    feats_contacted = extract_features(rel_contacted)
    
    rel_other = {"relationship_type": "SOME_OTHER_TYPE"}
    feats_other = extract_features(rel_other)
    
    # Verify different evidence leads to different frequency scoring
    assert feats_contacted[5] != feats_other[5]

def test_training_and_prediction():
    if os.path.exists(MODEL_PATH):
        os.remove(MODEL_PATH)
        
    data_path = os.path.join(os.path.dirname(__file__), '../data/ground_truth.csv')
    metrics = train_model(data_path)
    
    assert "accuracy" in metrics
    assert metrics["positive_examples_total"] > 0
    assert metrics["negative_examples_total"] > 0
    
    assert os.path.exists(MODEL_PATH)
    
    rel = {
        "source": "PERSON-017",
        "target": "PERSON-043",
        "relationship_type": "CONTACTED",
        "evidence": "PERSON-017 contacted PERSON-043 using PHONE-004.",
        "case_id": "CASE-001",
        "detection_method": "RULE"
    }
    
    pred = predict_confidence(rel)
    assert 0.0 <= pred["relationship_confidence"] <= 1.0
    assert pred["confidence_level"] in ["HIGH", "MEDIUM", "LOW"]

def test_invalid_evidence():
    rel = {
        "source": "PERSON-017",
        "target": "PERSON-043",
        "relationship_type": "CONTACTED",
        "evidence": "N/A", 
        "case_id": "",
        "detection_method": ""
    }
    feats = extract_features(rel)
    assert feats[1] == 0.0 # No evidence strength
    assert feats[2] == 0.0 # No keyword match

def test_model_deterministic_loading():
    model = joblib.load(MODEL_PATH)
    assert model.random_state == 42
