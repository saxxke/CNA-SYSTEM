"""
models.py
=========
Pydantic data models for the Step 21 AI Investigation Assistant.

Defines:
- Canonical intent enumeration
- Structured query schema
- Provenance reference schema
- Candidate disambiguation records
- Assistant request & grounded response models
"""

from enum import Enum
from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field

class AssistantResponseState(str, Enum):
    MATCH_FOUND = "MATCH_FOUND"
    NO_MATCH = "NO_MATCH"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    ANSWER = "ANSWER"


class AssistantIntent(str, Enum):
    PERSON_SEARCH = "PERSON_SEARCH"
    CASE_SEARCH = "CASE_SEARCH"
    PERSON_PROFILE = "PERSON_PROFILE"
    CASE_DETAILS = "CASE_DETAILS"
    NETWORK_QUERY = "NETWORK_QUERY"
    RELATED_CASES = "RELATED_CASES"
    PRIORITY_EXPLANATION = "PRIORITY_EXPLANATION"
    GENERAL_ANALYTICAL_QUERY = "GENERAL_ANALYTICAL_QUERY"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"


class StructuredAssistantQuery(BaseModel):
    intent: AssistantIntent
    confidence: float = 1.0
    
    # Target entities
    person_id: Optional[str] = None
    person_name: Optional[str] = None
    case_id: Optional[str] = None
    phone: Optional[str] = None
    vehicle: Optional[str] = None
    organization: Optional[str] = None
    biometric_id: Optional[str] = None
    
    # Filters
    offence: Optional[str] = None
    location: Optional[str] = None
    district: Optional[str] = None
    status: Optional[str] = None
    year: Optional[str] = None
    phone_prefix: Optional[str] = None
    phone_suffix: Optional[str] = None
    min_case_count: Optional[int] = None
    max_case_count: Optional[int] = None
    exact_case_count: Optional[int] = None
    
    # Explicit aspect requests
    requested_aspect: Optional[str] = None  # "CASES", "NETWORK", "PRIORITY", "FAMILY", "OVERVIEW"
    include_family: bool = False  # Only True if explicitly asked
    
    # Clarification/reasoning
    clarification_message: Optional[str] = None


class ProvenanceItem(BaseModel):
    source_type: str  # "CASE_RECORD", "PERSON_RECORD", "CASE_PERSON_ASSOCIATION", "SYNTHETIC_COMMUNICATION", "SYNTHETIC_TRANSACTION", "GRAPH_EDGE", "PRIORITY_ANALYSIS"
    source_id: str
    case_id: Optional[str] = None
    evidence_text: Optional[str] = None
    confidence: Optional[float] = None
    detection_method: Optional[str] = None


class PersonCandidate(BaseModel):
    person_id: str
    full_name: str
    location: str
    associated_case_count: int
    occupation: Optional[str] = ""
    aliases: List[str] = Field(default_factory=list)


class AssistantQueryRequest(BaseModel):
    question: str
    conversation_context: Optional[Union[List[Any], Dict[str, Any]]] = None
    active_case_id: Optional[str] = None
    active_person_id: Optional[str] = None


class AssistantQueryResponse(BaseModel):
    question: str
    intent: AssistantIntent
    response_state: AssistantResponseState = AssistantResponseState.ANSWER
    structured_query: StructuredAssistantQuery
    answer_markdown: str
    provenance: List[ProvenanceItem] = Field(default_factory=list)
    
    # Structured entity payloads for interactive UI rendering
    persons: List[Dict[str, Any]] = Field(default_factory=list)
    cases: List[Dict[str, Any]] = Field(default_factory=list)
    network_relationships: List[Dict[str, Any]] = Field(default_factory=list)
    priority_information: Optional[Dict[str, Any]] = None
    
    # Clarification choices if ambiguous
    candidates: List[PersonCandidate] = Field(default_factory=list)
    
    # Follow-up guidance
    suggested_followups: List[str] = Field(default_factory=list)
    safety_notice: str = "SYNTHETIC DEMONSTRATION DATA. Analytical lead only. Requires human verification."
