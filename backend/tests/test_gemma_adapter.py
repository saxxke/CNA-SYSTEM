"""
test_gemma_adapter.py
======================
Unit tests for the Google-hosted Gemma 4 LLM adapter (GemmaLLMClient) in CNA-SYSTEM.

Covers:
1. Provider selection and aliases (GEMMA, GEMMA4, GEMMA_4, MOCK fallback).
2. Missing API key and unavailable client behavior.
3. Valid structured intent JSON parsing into StructuredAssistantQuery.
4. Malformed JSON and invalid schema handling (safe None return).
5. Empty model responses, timeouts, and API exceptions (safe None return).
6. Grounded explanation generation with safety checks.
7. Safe fallback to deterministic responses when Gemma returns None.
8. Preservation of assistant security and retrieval-first gating (LLM never called on NO_MATCH or CLARIFICATION_REQUIRED).
"""

import os
import json
import pytest
from unittest.mock import MagicMock, patch

from modules.assistant.models import (
    AssistantIntent,
    AssistantResponseState,
    StructuredAssistantQuery,
    AssistantQueryResponse
)
from modules.assistant.llm_adapter import (
    BaseLLMClient,
    MockLLMClient,
    GemmaLLMClient,
    get_llm_client
)
from modules.assistant.assistant_service import process_assistant_query
from modules.graph.dataset_integration import build_dataset_graph
from modules.analytics.graph_analytics import analyze_graph
from modules.priority.priority_scorer import calculate_priority_scores


@pytest.fixture(scope="module")
def app_context():
    G = build_dataset_graph()
    analytics = analyze_graph(G)
    priority = calculate_priority_scores(G, analytics)
    return {"G": G, "analytics": analytics, "priority": priority}


# ==============================================================================
# 1. Provider Selection and Aliases
# ==============================================================================

def test_provider_selection_gemma_aliases():
    """Verify that GEMMA, GEMMA4, and GEMMA_4 all resolve to GemmaLLMClient when configured."""
    for alias in ["GEMMA", "gemma", "GEMMA4", "gemma4", "GEMMA_4", "gemma_4"]:
        with patch.dict(os.environ, {"ASSISTANT_LLM_PROVIDER": alias, "GEMMA_API_KEY": "fake_test_key"}):
            with patch("google.genai.Client") as mock_client:
                client = get_llm_client()
                assert isinstance(client, GemmaLLMClient)
                assert client.is_available()


def test_provider_selection_default_mock():
    """Verify that default or unset provider resolves to MockLLMClient."""
    with patch.dict(os.environ, {"ASSISTANT_LLM_PROVIDER": "MOCK"}, clear=False):
        client = get_llm_client()
        assert isinstance(client, MockLLMClient)

    # When provider is not set at all
    with patch.dict(os.environ, {}, clear=True):
        client = get_llm_client()
        assert isinstance(client, MockLLMClient)


# ==============================================================================
# 2. Missing API Key and Unavailable Client
# ==============================================================================

def test_missing_api_key_gemma_fallback():
    """Verify that GemmaLLMClient without API key is unavailable and get_llm_client falls back to Mock."""
    with patch.dict(os.environ, {"ASSISTANT_LLM_PROVIDER": "GEMMA"}, clear=True):
        # Explicitly initialize GemmaLLMClient without key
        client = GemmaLLMClient(api_key=None)
        assert not client.is_available()
        assert client.parse_query_intent("Who is Arjun Mehta?") is None
        assert client.synthesize_explanation("Who is Arjun Mehta?", {}) is None

        # Factory should fall back safely to MockLLMClient
        fallback_client = get_llm_client()
        assert isinstance(fallback_client, MockLLMClient)


def test_api_key_fallback_chain():
    """Verify that GEMMA_API_KEY falls back to GEMINI_API_KEY, GOOGLE_API_KEY, or ASSISTANT_API_KEY."""
    # Test GEMINI_API_KEY fallback
    with patch.dict(os.environ, {"GEMINI_API_KEY": "test_gemini_key"}, clear=True):
        with patch("google.genai.Client"):
            client = GemmaLLMClient()
            assert client.api_key == "test_gemini_key"
            assert client.is_available()

    # Test GOOGLE_API_KEY fallback
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_google_key"}, clear=True):
        with patch("google.genai.Client"):
            client = GemmaLLMClient()
            assert client.api_key == "test_google_key"
            assert client.is_available()


# ==============================================================================
# 3. Valid Structured Intent JSON Parsing
# ==============================================================================

def test_valid_structured_intent_json():
    """Verify that a valid JSON response from Gemma is parsed into StructuredAssistantQuery."""
    valid_payload = {
        "intent": "PERSON_SEARCH",
        "person_id": None,
        "person_name": None,
        "case_id": None,
        "offence": "Kidnapping",
        "location": "Kolkata",
        "district": None,
        "status": None,
        "phone_prefix": None,
        "phone_suffix": None,
        "min_case_count": None,
        "max_case_count": None,
        "exact_case_count": None,
        "requested_aspect": None
    }

    mock_response = MagicMock()
    mock_response.text = f"```json\n{json.dumps(valid_payload)}\n```"

    with patch("google.genai.Client") as mock_client_cls:
        mock_genai_instance = MagicMock()
        mock_genai_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_genai_instance

        client = GemmaLLMClient(api_key="fake_key")
        result = client.parse_query_intent("Show persons associated with kidnapping cases in Kolkata.")

        assert result is not None
        assert isinstance(result, StructuredAssistantQuery)
        assert result.intent == AssistantIntent.PERSON_SEARCH
        assert result.offence == "Kidnapping"
        assert result.location == "Kolkata"


# ==============================================================================
# 4. Malformed JSON and Invalid Schema Values
# ==============================================================================

def test_malformed_json_returns_none():
    """Verify that malformed JSON from model gracefully returns None without raising exceptions."""
    mock_response = MagicMock()
    mock_response.text = "This is not valid JSON at all: {broken: true,"

    with patch("google.genai.Client") as mock_client_cls:
        mock_genai_instance = MagicMock()
        mock_genai_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_genai_instance

        client = GemmaLLMClient(api_key="fake_key")
        result = client.parse_query_intent("Find suspect")
        assert result is None


def test_invalid_enum_value_returns_none():
    """Verify that an invalid intent enum value returns None rather than crashing."""
    invalid_payload = {
        "intent": "FABRICATED_UNSUPPORTED_INTENT",
        "person_id": None
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(invalid_payload)

    with patch("google.genai.Client") as mock_client_cls:
        mock_genai_instance = MagicMock()
        mock_genai_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_genai_instance

        client = GemmaLLMClient(api_key="fake_key")
        result = client.parse_query_intent("Test invalid intent")
        assert result is None


# ==============================================================================
# 5. Empty Model Responses and API Exceptions
# ==============================================================================

def test_empty_model_response():
    """Verify that an empty response or response with no text returns None."""
    mock_response = MagicMock()
    mock_response.text = ""

    with patch("google.genai.Client") as mock_client_cls:
        mock_genai_instance = MagicMock()
        mock_genai_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_genai_instance

        client = GemmaLLMClient(api_key="fake_key")
        assert client.parse_query_intent("Hello") is None
        assert client.synthesize_explanation("Hello", {}) is None


def test_api_exception_handling():
    """Verify that network errors and API exceptions are caught and return None."""
    with patch("google.genai.Client") as mock_client_cls:
        mock_genai_instance = MagicMock()
        mock_genai_instance.models.generate_content.side_effect = RuntimeError("API connection timed out")
        mock_client_cls.return_value = mock_genai_instance

        client = GemmaLLMClient(api_key="fake_key")
        assert client.parse_query_intent("Query") is None
        assert client.synthesize_explanation("Query", {}) is None


# ==============================================================================
# 6. Grounded Explanation Generation & Prohibited Terminology
# ==============================================================================

def test_synthesize_explanation_success():
    """Verify that synthesize_explanation returns sanitized text generated by Gemma."""
    mock_response = MagicMock()
    mock_response.text = "Arjun Mehta is associated with 4 registered case records in Raipur and Kolkata."

    with patch("google.genai.Client") as mock_client_cls:
        mock_genai_instance = MagicMock()
        mock_genai_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_genai_instance

        client = GemmaLLMClient(api_key="fake_key")
        facts = {"person_id": "PERSON-001", "name": "Arjun Mehta", "cases": ["CASE-001"]}
        explanation = client.synthesize_explanation("Tell me about Arjun Mehta", facts)

        assert explanation is not None
        assert "Arjun Mehta" in explanation
        assert "associated with 4 registered case records" in explanation


def test_synthesize_explanation_sanitizes_prohibited_terms():
    """Verify defense-in-depth: prohibited terms are replaced with neutral investigative phrasing."""
    mock_response = MagicMock()
    mock_response.text = "Subject is a confirmed criminal and guilty of fraud in Raipur."

    with patch("google.genai.Client") as mock_client_cls:
        mock_genai_instance = MagicMock()
        mock_genai_instance.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_genai_instance

        client = GemmaLLMClient(api_key="fake_key")
        explanation = client.synthesize_explanation("Question", {"data": "test"})

        assert "confirmed criminal" not in explanation
        assert "guilty of" not in explanation
        assert "individual associated with case records" in explanation


# ==============================================================================
# 7. Safe Fallback to Deterministic Responses
# ==============================================================================

def test_safe_fallback_when_gemma_fails(app_context):
    """Verify that if Gemma fails, assistant_service uses deterministic response generator seamlessly."""
    failing_client = MagicMock(spec=BaseLLMClient)
    failing_client.parse_query_intent.return_value = None  # Force rule engine
    failing_client.synthesize_explanation.return_value = None  # Force deterministic response

    res = process_assistant_query(
        "Tell me more about Arjun Mehta.",
        G=app_context["G"],
        analytics=app_context["analytics"],
        priority=app_context["priority"],
        llm_client=failing_client
    )

    assert res.response_state == AssistantResponseState.MATCH_FOUND
    assert res.intent == AssistantIntent.PERSON_PROFILE
    assert len(res.persons) == 1
    assert res.persons[0]["full_name"] == "Arjun Mehta"
    # Deterministic answer was generated
    assert len(res.answer_markdown) > 0
    assert "Arjun Mehta" in res.answer_markdown
    assert len(res.provenance) > 0


# ==============================================================================
# 8. Preservation of Security & Retrieval-First Gating
# ==============================================================================

def test_retrieval_first_gating_never_calls_synthesis_on_no_match(app_context):
    """
    CRITICAL ANTI-HALLUCINATION TEST:
    Verify that synthesize_explanation is NEVER called if retrieval returns NO_MATCH.
    """
    mock_client = MagicMock(spec=BaseLLMClient)
    mock_client.parse_query_intent.return_value = None  # Use deterministic parser
    mock_client.synthesize_explanation.return_value = "Fabricated profile of Rahul Banerjee"

    res = process_assistant_query(
        "Show me the profile of Rahul Banerjee",  # Non-existent person
        G=app_context["G"],
        analytics=app_context["analytics"],
        priority=app_context["priority"],
        llm_client=mock_client
    )

    assert res.response_state == AssistantResponseState.NO_MATCH
    # synthesize_explanation MUST NOT have been called
    mock_client.synthesize_explanation.assert_not_called()
    assert "no matching person was found" in res.answer_markdown.lower()
    assert "Fabricated" not in res.answer_markdown


def test_retrieval_first_gating_never_calls_synthesis_on_clarification(app_context):
    """
    CRITICAL ANTI-HALLUCINATION TEST:
    Verify that synthesize_explanation is NEVER called if retrieval returns CLARIFICATION_REQUIRED.
    """
    mock_client = MagicMock(spec=BaseLLMClient)
    mock_client.parse_query_intent.return_value = None
    mock_client.synthesize_explanation.return_value = "Fabricated choice"

    res = process_assistant_query(
        "Tell me about Arjun",  # Ambiguous: Arjun Mehta vs Arjun Sen
        G=app_context["G"],
        analytics=app_context["analytics"],
        priority=app_context["priority"],
        llm_client=mock_client
    )

    assert res.response_state == AssistantResponseState.CLARIFICATION_REQUIRED
    mock_client.synthesize_explanation.assert_not_called()
    assert len(res.candidates) > 1
    assert "I found multiple matching people" in res.answer_markdown
