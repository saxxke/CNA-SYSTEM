"""
models.py
=========
Pydantic data models for Phase 8A: Relationship Evidence Provenance.

Strict Privacy & Sanitization:
- ZERO raw_fields or open-ended dictionaries.
- Strongly typed, explicitly sanitized synthetic demonstration records.
- Strict non-accusatory terminology: Confidence Evidence Breakdown.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class DetectionMethod(str, Enum):
    STRUCTURED_METADATA = "STRUCTURED_METADATA"
    RULE = "RULE"
    TELECOM_ANALYSIS = "TELECOM_ANALYSIS"
    BANKING_ANALYSIS = "BANKING_ANALYSIS"
    ML_CONFIDENCE = "ML_CONFIDENCE"
    CROSS_RECORD_LINKAGE = "CROSS_RECORD_LINKAGE"


# Explicitly Sanitized Supporting Records (Strictly No raw_fields)
class SanitizedCommunicationRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    record_id: str
    record_type: str = "COMMUNICATION"
    case_id: str
    source_person_id: str
    target_person_id: str
    communication_type: str
    date: str
    duration_seconds: int
    summary: str


class SanitizedTransactionRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    record_id: str
    record_type: str = "TRANSACTION"
    case_id: str
    source_person_id: str
    target_person_id: str
    amount: float
    currency: str
    date: str
    summary: str


class SanitizedCaseAssociationRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    record_id: str
    record_type: str = "CASE_ASSOCIATION"
    case_id: str
    person_id: str
    role: str
    summary: str


class SanitizedMetadataLinkageRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    record_id: str
    record_type: str = "METADATA_LINKAGE"
    case_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    evidence_reference: str
    summary: str


class SupportingRecordWrapper(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    record_type: str
    communication: Optional[SanitizedCommunicationRecord] = None
    transaction: Optional[SanitizedTransactionRecord] = None
    case_association: Optional[SanitizedCaseAssociationRecord] = None
    metadata_linkage: Optional[SanitizedMetadataLinkageRecord] = None


class ObservableSignal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    feature_name: str
    feature_value: float
    signal_interpretation: str


class ConfidenceEvidenceBreakdown(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    confidence_score: float
    confidence_level: str  # HIGH, MEDIUM, LOW
    observable_signals: List[ObservableSignal]
    model_family: str = "Logistic Regression"
    methodology_note: str = (
        "Confidence is an algorithmic estimate based on observed corroborating evidence in the synthetic dataset. "
        "It does NOT represent proof, criminal probability, or guilt. Human verification required."
    )


class EdgeProvenanceResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    source_id: str
    source_label: str
    source_type: str
    target_id: str
    target_label: str
    target_type: str
    relationship_type: str
    case_id: str
    detection_method: DetectionMethod
    confidence_breakdown: ConfidenceEvidenceBreakdown
    supporting_records: List[SupportingRecordWrapper]
    safety_disclaimer: str = (
        "SYNTHETIC DEMONSTRATION DATA • Potential Relationship • "
        "Analytical lead only. Requires human verification. Does not determine guilt or criminality."
    )
