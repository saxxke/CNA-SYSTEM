"""
llm_adapter.py
==============
Provider-agnostic LLM interface for the Step 21 AI Investigation Assistant.

Features:
- BaseLLMClient abstract class.
- MockLLMClient (default, fully deterministic, offline, zero API keys required).
- Optional GeminiLLMClient (invoked only if google-generativeai / API key is present).
- The rest of the system NEVER depends on a specific provider or external network availability.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from modules.assistant.models import StructuredAssistantQuery, AssistantIntent

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract interface for LLM operations in PS26189."""

    @abstractmethod
    def parse_query_intent(self, question: str, context: Optional[Dict[str, Any]] = None) -> Optional[StructuredAssistantQuery]:
        """Convert natural language investigator question into a StructuredAssistantQuery."""
        pass

    @abstractmethod
    def synthesize_explanation(self, question: str, retrieved_facts: Dict[str, Any]) -> Optional[str]:
        """Format retrieved structured records into a readable grounded response without inventing facts."""
        pass


class MockLLMClient(BaseLLMClient):
    """
    Default mock/deterministic adapter.
    Ensures 100% offline testability, zero external dependencies, and zero cost.
    """

    def parse_query_intent(self, question: str, context: Optional[Dict[str, Any]] = None) -> Optional[StructuredAssistantQuery]:
        # Return None so the fast-path deterministic rule engine performs the parsing
        return None

    def synthesize_explanation(self, question: str, retrieved_facts: Dict[str, Any]) -> Optional[str]:
        # Return None so the deterministic response generator formats the response directly
        return None


class GeminiLLMClient(BaseLLMClient):
    """
    Optional adapter for Google Gemini API.
    Only loaded if `google.generativeai` is installed AND `GEMINI_API_KEY` (or `ASSISTANT_API_KEY`) is set.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("ASSISTANT_API_KEY")
        self.model_name = model_name
        self.client = None

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini model: {e}")
                self.client = None

    def is_available(self) -> bool:
        return self.client is not None

    def parse_query_intent(self, question: str, context: Optional[Dict[str, Any]] = None) -> Optional[StructuredAssistantQuery]:
        if not self.is_available():
            return None

        prompt = f"""
        You are a query understanding assistant for a law enforcement intelligence analysis system.
        Classify the investigator question into one of the following intents:
        PERSON_SEARCH, CASE_SEARCH, PERSON_PROFILE, CASE_DETAILS, NETWORK_QUERY, RELATED_CASES, PRIORITY_EXPLANATION, GENERAL_ANALYTICAL_QUERY, CLARIFICATION_REQUIRED, UNSUPPORTED.

        Return ONLY a raw JSON object matching the following schema:
        {{
            "intent": "<INTENT>",
            "person_id": "<PERSON-ID or null>",
            "person_name": "<Person Name or null>",
            "case_id": "<CASE-ID or null>",
            "offence": "<Offence category or null>",
            "location": "<Location or null>",
            "district": "<District or null>",
            "status": "<Status or null>",
            "phone_prefix": "<Digits or null>",
            "phone_suffix": "<Digits or null>",
            "min_case_count": <Integer or null>,
            "max_case_count": <Integer or null>,
            "exact_case_count": <Integer or null>,
            "requested_aspect": "<CASES|NETWORK|PRIORITY|FAMILY|OVERVIEW|null>"
        }}

        Do NOT invent IDs. If unsure or if query is not about investigation records, mark as UNSUPPORTED.
        Question: "{question}"
        """
        try:
            response = self.client.generate_content(prompt)
            text = response.text.strip()
            # Clean markdown fenced blocks if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
            return StructuredAssistantQuery(**data)
        except Exception as e:
            logger.warning(f"Gemini parse_query_intent failed: {e}. Falling back to deterministic parser.")
            return None

    def synthesize_explanation(self, question: str, retrieved_facts: Dict[str, Any]) -> Optional[str]:
        if not self.is_available():
            return None

        prompt = f"""
        You are an AI Investigation Assistant reporting deterministic intelligence records.
        CRITICAL SAFETY RULES:
        1. Use ONLY the facts provided in the JSON payload. NEVER invent or assume facts, persons, cases, phone numbers, or graph connections.
        2. Strictly NEVER use words like "criminal", "guilty", "convicted", or "confirmed criminal".
        3. Use neutral investigative phrasing: "associated with case records", "potential relationship", "investigative lead", "analytical priority".
        4. Refer to telecom/transaction logs as "synthetic communication record" or "synthetic transaction record".
        5. Family relationships must NEVER imply guilt or case involvement.

        Question: "{question}"
        Retrieved Facts: {json.dumps(retrieved_facts, default=str)}
        """
        try:
            response = self.client.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini synthesize_explanation failed: {e}. Falling back to deterministic generator.")
            return None


def get_llm_client() -> BaseLLMClient:
    """
    Factory function for obtaining the configured LLM client.
    Defaults to MockLLMClient (100% offline, zero keys needed).
    """
    provider = os.environ.get("ASSISTANT_LLM_PROVIDER", "MOCK").upper().strip()
    if provider == "GEMINI":
        client = GeminiLLMClient()
        if client.is_available():
            return client
    return MockLLMClient()
