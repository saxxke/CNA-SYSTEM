from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class HealthResponse(BaseModel):
    status: str

class SummaryResponse(BaseModel):
    total_cases: int
    total_entities: int
    total_relationships: int
    total_network_nodes: int
    node_counts_by_type: Dict[str, int]
    relationship_counts_by_type: Dict[str, int]

class Case(BaseModel):
    id: str
    type: str
    details: Dict[str, Any]

class Entity(BaseModel):
    id: str
    type: str
    value: Optional[str] = None
    details: Dict[str, Any]

class Edge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    confidence: float
    evidence: str
    case_id: str
    detection_method: str

class Node(BaseModel):
    id: str
    label: str
    type: str

class GraphResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

class PriorityResult(BaseModel):
    entity_id: str
    entity_type: str
    priority_score: float
    priority_level: str
    reasons: List[str]
    supporting_evidence: List[str]

class SearchResult(BaseModel):
    id: str
    type: str
    label: str
    match_type: str

class SearchResponse(BaseModel):
    results: List[SearchResult]

# --- Step 20: Advanced Search & Investigation Filtering Models ---

class AdvancedSearchRequest(BaseModel):
    mode: Optional[str] = "ALL"  # "ALL", "PERSON", "CASE"
    query: Optional[str] = None
    name: Optional[str] = None
    alias: Optional[str] = None
    person_id: Optional[str] = None
    case_id: Optional[str] = None
    fir_number: Optional[str] = None
    offence: Optional[str] = None
    legal_section: Optional[str] = None
    location: Optional[str] = None
    district: Optional[str] = None
    police_station: Optional[str] = None
    status: Optional[str] = None
    year: Optional[str] = None
    phone: Optional[str] = None
    phone_prefix: Optional[str] = None
    phone_suffix: Optional[str] = None
    vehicle: Optional[str] = None
    organization: Optional[str] = None
    occupation: Optional[str] = None
    min_case_count: Optional[int] = None
    max_case_count: Optional[int] = None
    exact_case_count: Optional[int] = None
    limit: Optional[int] = 100

class PersonSearchResultItem(BaseModel):
    person_id: str
    full_name: str
    aliases: List[str]
    gender: str
    age: Optional[Any] = ""
    occupation: str
    phone_number: str
    district: str
    city: str
    associated_case_count: int
    matching_case_ids: List[str]
    matching_reasons: List[str]
    threat_level: str

class CaseSearchResultItem(BaseModel):
    case_id: str
    title: str
    fir_number: str
    offence_category: str
    legal_section: str
    date_opened: str
    year: str
    district: str
    police_station: str
    status: str
    associated_persons_count: int
    matching_reasons: List[str]

class AdvancedSearchResponse(BaseModel):
    mode: str
    total_persons: int
    total_cases: int
    total_results: int
    persons: List[PersonSearchResultItem]
    cases: List[CaseSearchResultItem]
    safety_notice: str


# --- Step 27: Case Registration & Entity Resolution Models ---

class CaseDetailsInput(BaseModel):
    title: str
    offence_category: str
    incident_date: str
    location: str
    district: str
    police_station: str
    description: str
    status: Optional[str] = "OPEN"
    fir_number: Optional[str] = None
    legal_section: Optional[str] = None
    incident_time: Optional[str] = None
    state: Optional[str] = "Chhattisgarh"
    additional_notes: Optional[str] = None

class NewPersonDataInput(BaseModel):
    full_name: str
    gender: Optional[str] = "Unknown"
    date_of_birth: Optional[str] = None
    age: Optional[str] = None
    occupation: Optional[str] = None
    education: Optional[str] = None
    address: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = "Chhattisgarh"
    pin_code: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    alias: Optional[str] = None

class AssociatedPersonInput(BaseModel):
    person_type: str  # "EXISTING" or "NEW"
    role: str         # "SUBJECT", "PERSON_OF_INTEREST", "WITNESS", etc.
    person_id: Optional[str] = None
    new_person_data: Optional[NewPersonDataInput] = None

class OptionalEntityInput(BaseModel):
    entity_type: str  # "PHONE", "VEHICLE", "BANK_ACCOUNT"
    value: str
    vehicle_type: Optional[str] = None
    bank_name: Optional[str] = None

class RegisterCaseRequest(BaseModel):
    case: CaseDetailsInput
    associated_persons: List[AssociatedPersonInput]
    optional_entities: Optional[List[OptionalEntityInput]] = []

class AssociatedPersonSummary(BaseModel):
    cp_id: str
    case_id: str
    person_id: str
    person_name: str
    role: str
    is_new: bool

class RegisterCaseResponse(BaseModel):
    success: bool
    message: str
    case_id: str
    case_title: str
    created_case: Dict[str, Any]
    associated_persons: List[AssociatedPersonSummary]
    graph_summary: Dict[str, int]

class DuplicateCheckRequest(BaseModel):
    full_name: str
    phone: Optional[str] = None
    district: Optional[str] = None

class DuplicateCandidateMatch(BaseModel):
    person_id: str
    full_name: str
    district: str
    occupation: str
    phone_number: str
    score: float
    match_level: str  # "DUPLICATE" or "POSSIBLE_MATCH"
    match_type: str
    reason: str

class DuplicateCheckResponse(BaseModel):
    has_matches: bool
    matches: List[DuplicateCandidateMatch]


# --- Phase 1 & 2: Authentication & User Models ---

from modules.auth.roles import UserRole
from modules.auth.models import User, UserPublic, UserCreate


class LoginRequest(BaseModel):
    """
    Credentials submitted to POST /api/auth/login.
    Role or user_id fields supplied by client are never used.
    """
    username: str
    password: str

    @classmethod
    def validate_non_empty(cls, v: str, field_name: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"{field_name} cannot be empty.")
        return v.strip()


class LoginResponse(BaseModel):
    """
    Successful authentication response with bearer session token.
    Never exposes password_hash or plaintext password.
    """
    token: str
    token_type: str = "bearer"
    user: UserPublic


class LogoutResponse(BaseModel):
    """
    Logout response confirming session token invalidation.
    """
    success: bool = True
    message: str = "Successfully logged out."


# --- Phase 4: Citizen Object-Level Authorization Models ---

class CitizenSafeCaseItem(BaseModel):
    """
    Sanitized, citizen-facing case status information.
    Excludes all internal investigative notes, networks, evidence, suspects, and priority scores.
    """
    case_id: str
    case_title: str
    offence_category: str
    fir_number: Optional[str] = None
    date_opened: Optional[str] = None
    status: str
    police_station: str
    district: str
    state: str
    official_notice: str = "Authorized citizen case inquiry record. For queries, contact your local police station."
    authorized_for_user: str





