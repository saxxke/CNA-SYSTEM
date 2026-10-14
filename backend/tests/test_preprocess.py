import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.nlp.preprocess import clean_text, normalize_whitespace, sentence_segmentation, basic_tokenization, preprocess

def test_empty_null_input():
    assert clean_text(None) == ""
    assert clean_text("") == ""
    assert normalize_whitespace(None) == ""
    assert normalize_whitespace("") == ""
    assert sentence_segmentation(None) == []
    assert sentence_segmentation("") == []
    assert basic_tokenization(None) == []
    assert basic_tokenization("") == []

def test_whitespace_normalization():
    dirty_text = "This   is  a\n\ntest\tstring."
    cleaned = normalize_whitespace(dirty_text)
    assert cleaned == "This is a test string."

def test_sentence_segmentation():
    text = "First sentence. Second sentence! Is this a third?"
    sentences = sentence_segmentation(text)
    assert len(sentences) == 3
    assert sentences[0] == "First sentence."
    assert sentences[1] == "Second sentence!"
    assert sentences[2] == "Is this a third?"

def test_basic_tokenization():
    text = "Hello, world!"
    tokens = basic_tokenization(text)
    # Both spacy and fallback regex should separate punctuation
    assert "Hello" in tokens
    assert "," in tokens
    assert "world" in tokens
    assert "!" in tokens

def test_preservation_identifiers():
    # Identifiers should not be destroyed by clean or normalize
    text = "Case CASE-001 involves phone +91 9000000004."
    cleaned = clean_text(text)
    assert "CASE-001" in cleaned
    assert "+91 9000000004" in cleaned
    
    bank_text = "Bank account BANK-023 transferred funds."
    assert "BANK-023" in clean_text(bank_text)
    
    vehicle_text = "Vehicle WB00XX0001 seen."
    assert "WB00XX0001" in clean_text(vehicle_text)
    
def test_full_pipeline():
    text = "  The suspect in CASE-001 \n\n used vehicle WB00XX0001. He called +91 9000000004!  "
    result = preprocess(text)
    assert result["original_text"] == text
    assert result["normalized_text"] == "The suspect in CASE-001 used vehicle WB00XX0001. He called +91 9000000004!"
    assert len(result["sentences"]) == 2
    assert "WB00XX0001" in result["normalized_text"]
    assert "CASE-001" in result["normalized_text"]
    assert "+91" in result["normalized_text"]
