"""
provenance_service.py
=====================
Core service for retrieving and structuring explainable evidence provenance
for knowledge graph edges in Phase 8A.

Strict Constraints:
- No raw_fields or open-ended dictionaries.
- Strict non-accusatory terminology: Confidence Evidence Breakdown.
- Grounded strictly in synthetic demonstration records.
"""

from typing import Optional, List, Dict, Any
import networkx as nx

from data.validate_dataset import load_csv
from modules.ml.relationship_confidence import extract_features
from modules.provenance.models import (
    DetectionMethod,
    SanitizedCommunicationRecord,
    SanitizedTransactionRecord,
    SanitizedCaseAssociationRecord,
    SanitizedMetadataLinkageRecord,
    SupportingRecordWrapper,
    ObservableSignal,
    ConfidenceEvidenceBreakdown,
    EdgeProvenanceResponse,
)

# In-memory cached dataset indexes for fast, sanitized lookups
_RECORDS_CACHE: Optional[Dict[str, Any]] = None


def _get_records_cache() -> Dict[str, Any]:
    global _RECORDS_CACHE
    if _RECORDS_CACHE is not None:
        return _RECORDS_CACHE

    raw_comms = load_csv("communications.csv") or []
    raw_txns = load_csv("transactions.csv") or []
    raw_cps = load_csv("case_persons.csv") or []
    raw_gt = load_csv("ground_truth.csv") or []

    comms_by_id = {c.get("communication_id"): c for c in raw_comms if c.get("communication_id")}
    txns_by_id = {t.get("transaction_id"): t for t in raw_txns if t.get("transaction_id")}
    gt_by_id = {g.get("ground_truth_id"): g for g in raw_gt if g.get("ground_truth_id")}

    _RECORDS_CACHE = {
        "raw_comms": raw_comms,
        "raw_txns": raw_txns,
        "raw_cps": raw_cps,
        "raw_gt": raw_gt,
        "comms_by_id": comms_by_id,
        "txns_by_id": txns_by_id,
        "gt_by_id": gt_by_id,
    }
    return _RECORDS_CACHE


SIGNAL_DESCRIPTIONS = {
    "entity_similarity": "Orthographic label similarity score between entities",
    "text_evidence_strength": "Normalized length of the extracted evidence statement",
    "relationship_keyword_match": "Corroborated by deterministic syntactical pattern matching",
    "supporting_record_count": "Count of corroborating co-occurrences in synthetic records",
    "source_record_count": "Frequency of source entity presence across dataset records",
    "relationship_frequency": "Standard frequency index for this relationship category",
    "cross_case_connectivity": "Number of distinct case records associated with source entity",
}


def _build_observable_signals(features_dict: Dict[str, float]) -> List[ObservableSignal]:
    signals = []
    for k, val in features_dict.items():
        desc = SIGNAL_DESCRIPTIONS.get(k, "Extracted observable evidence signal")
        signals.append(
            ObservableSignal(
                feature_name=k,
                feature_value=float(round(val, 4)),
                signal_interpretation=desc,
            )
        )
    return signals


def _resolve_sanitized_records(
    record_ids: List[str],
    source_id: str,
    target_id: str,
    case_id: str
) -> List[SupportingRecordWrapper]:
    cache = _get_records_cache()
    wrappers: List[SupportingRecordWrapper] = []
    seen_keys = set()

    # 1. Lookup by explicit record IDs
    for rid in record_ids:
        if not rid:
            continue
        if rid in cache["comms_by_id"]:
            c = cache["comms_by_id"][rid]
            key = ("COMM", rid)
            if key not in seen_keys:
                seen_keys.add(key)
                rec = SanitizedCommunicationRecord(
                    record_id=rid,
                    case_id=c.get("case_id", ""),
                    source_person_id=c.get("source_person_id", ""),
                    target_person_id=c.get("target_person_id", ""),
                    communication_type=c.get("communication_type", "COMMUNICATION"),
                    date=c.get("date", ""),
                    duration_seconds=int(c.get("duration_seconds") or 0),
                    summary=c.get("description", "Telecommunication record linked to case.")
                )
                wrappers.append(SupportingRecordWrapper(record_type="COMMUNICATION", communication=rec))

        elif rid in cache["txns_by_id"]:
            t = cache["txns_by_id"][rid]
            key = ("TXN", rid)
            if key not in seen_keys:
                seen_keys.add(key)
                rec = SanitizedTransactionRecord(
                    record_id=rid,
                    case_id=t.get("case_id", ""),
                    source_person_id=t.get("source_person_id", ""),
                    target_person_id=t.get("target_person_id", ""),
                    amount=float(t.get("amount") or 0.0),
                    currency=t.get("currency", "INR"),
                    date=t.get("date", ""),
                    summary=t.get("description", "Financial transaction record linked to case.")
                )
                wrappers.append(SupportingRecordWrapper(record_type="TRANSACTION", transaction=rec))

        elif rid in cache["gt_by_id"]:
            g = cache["gt_by_id"][rid]
            key = ("GT", rid)
            if key not in seen_keys:
                seen_keys.add(key)
                rec = SanitizedMetadataLinkageRecord(
                    record_id=rid,
                    case_id=g.get("case_id", ""),
                    source_entity_id=g.get("source_entity_id", ""),
                    target_entity_id=g.get("target_entity_id", ""),
                    relationship_type=g.get("relationship_type", "INVOLVED_IN"),
                    evidence_reference=g.get("evidence_reference", "Synthetic metadata registry"),
                    summary=f"Structured ground truth linkage from {g.get('evidence_reference', 'case metadata')}."
                )
                wrappers.append(SupportingRecordWrapper(record_type="METADATA_LINKAGE", metadata_linkage=rec))

        elif rid.startswith("CP-"):
            parts = rid.split("-")
            cid = parts[1] if len(parts) > 1 else case_id
            pid = parts[2] if len(parts) > 2 else target_id
            key = ("CP", rid)
            if key not in seen_keys:
                seen_keys.add(key)
                rec = SanitizedCaseAssociationRecord(
                    record_id=rid,
                    case_id=cid,
                    person_id=pid,
                    role="ASSOCIATE",
                    summary=f"Official case-person association record for {pid} in {cid}."
                )
                wrappers.append(SupportingRecordWrapper(record_type="CASE_ASSOCIATION", case_association=rec))

    # 2. Corroborating lookups by participant pairs if wrappers is still empty
    if not wrappers:
        # Check communications between source and target
        for c in cache["raw_comms"]:
            c_src = c.get("source_person_id")
            c_tgt = c.get("target_person_id")
            if (c_src == source_id and c_tgt == target_id) or (c_src == target_id and c_tgt == source_id):
                rid = c.get("communication_id")
                key = ("COMM", rid)
                if key not in seen_keys:
                    seen_keys.add(key)
                    rec = SanitizedCommunicationRecord(
                        record_id=rid,
                        case_id=c.get("case_id", ""),
                        source_person_id=c_src or "",
                        target_person_id=c_tgt or "",
                        communication_type=c.get("communication_type", "COMMUNICATION"),
                        date=c.get("date", ""),
                        duration_seconds=int(c.get("duration_seconds") or 0),
                        summary=c.get("description", "Telecommunication record linked to case.")
                    )
                    wrappers.append(SupportingRecordWrapper(record_type="COMMUNICATION", communication=rec))

        # Check transactions between source and target
        for t in cache["raw_txns"]:
            t_src = t.get("source_person_id")
            t_tgt = t.get("target_person_id")
            if (t_src == source_id and t_tgt == target_id) or (t_src == target_id and t_tgt == source_id):
                rid = t.get("transaction_id")
                key = ("TXN", rid)
                if key not in seen_keys:
                    seen_keys.add(key)
                    rec = SanitizedTransactionRecord(
                        record_id=rid,
                        case_id=t.get("case_id", ""),
                        source_person_id=t_src or "",
                        target_person_id=t_tgt or "",
                        amount=float(t.get("amount") or 0.0),
                        currency=t.get("currency", "INR"),
                        date=t.get("date", ""),
                        summary=t.get("description", "Financial transaction record linked to case.")
                    )
                    wrappers.append(SupportingRecordWrapper(record_type="TRANSACTION", transaction=rec))

        # Check case_persons for CASE <-> PERSON links
        if source_id.startswith("CASE") or target_id.startswith("CASE"):
            cid = source_id if source_id.startswith("CASE") else target_id
            pid = target_id if source_id.startswith("CASE") else source_id
            for cp in cache["raw_cps"]:
                if cp.get("case_id") == cid and cp.get("person_id") == pid:
                    rid = f"CP-{cid}-{pid}"
                    key = ("CP", rid)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        rec = SanitizedCaseAssociationRecord(
                            record_id=rid,
                            case_id=cid,
                            person_id=pid,
                            role=cp.get("role", "ASSOCIATE"),
                            summary=cp.get("association", f"Official case association from case_persons.csv as {cp.get('role', 'ASSOCIATE')}.")
                        )
                        wrappers.append(SupportingRecordWrapper(record_type="CASE_ASSOCIATION", case_association=rec))

    return wrappers


def get_edge_provenance(
    G: nx.MultiDiGraph,
    source_id: str,
    target_id: str,
    case_id: Optional[str] = None
) -> Optional[EdgeProvenanceResponse]:
    """
    Retrieves and constructs the strictly sanitized evidence provenance
    for a directed or undirected edge between source_id and target_id.
    """
    if G is None or not G.has_node(source_id) or not G.has_node(target_id):
        return None

    # Search for edge in forward or reverse direction
    edge_data = None
    actual_source = source_id
    actual_target = target_id

    if G.has_edge(source_id, target_id):
        for k, d in G[source_id][target_id].items():
            if not case_id or d.get("case_id") == case_id:
                edge_data = d
                break
        if edge_data is None:
            # Take the first edge if case_id didn't match strictly
            edge_data = next(iter(G[source_id][target_id].values()))

    elif G.has_edge(target_id, source_id):
        actual_source = target_id
        actual_target = source_id
        for k, d in G[target_id][source_id].items():
            if not case_id or d.get("case_id") == case_id:
                edge_data = d
                break
        if edge_data is None:
            edge_data = next(iter(G[target_id][source_id].values()))

    if edge_data is None:
        return None

    # Source & Target Node metadata
    s_node = G.nodes.get(actual_source, {})
    t_node = G.nodes.get(actual_target, {})

    s_label = s_node.get("label") or s_node.get("value") or actual_source
    s_type = s_node.get("type", "ENTITY")
    t_label = t_node.get("label") or t_node.get("value") or actual_target
    t_type = t_node.get("type", "ENTITY")

    rel_type = edge_data.get("relationship_type", "ASSOCIATED_WITH")
    edge_case_id = edge_data.get("case_id", case_id or "")
    raw_det_method = edge_data.get("detection_method", "RULE")
    
    # Map detection method safely
    try:
        det_method = DetectionMethod(raw_det_method)
    except ValueError:
        det_method = DetectionMethod.RULE

    confidence_score = float(edge_data.get("confidence", 0.85))
    if confidence_score >= 0.80:
        conf_level = "HIGH"
    elif confidence_score >= 0.60:
        conf_level = "MEDIUM"
    else:
        conf_level = "LOW"

    # Extract or compute observable features
    features_dict = edge_data.get("features", {})
    if not features_dict:
        # Fallback to computing deterministic feature vector
        candidate_rel = {
            "source": actual_source,
            "target": actual_target,
            "relationship_type": rel_type,
            "case_id": edge_case_id,
            "evidence": edge_data.get("evidence", ""),
            "detection_method": raw_det_method
        }
        feats = extract_features(candidate_rel)
        feature_names = [
            "entity_similarity", "text_evidence_strength", "relationship_keyword_match",
            "supporting_record_count", "source_record_count", "relationship_frequency",
            "cross_case_connectivity"
        ]
        features_dict = dict(zip(feature_names, feats))

    observable_signals = _build_observable_signals(features_dict)

    confidence_breakdown = ConfidenceEvidenceBreakdown(
        confidence_score=round(confidence_score, 4),
        confidence_level=conf_level,
        observable_signals=observable_signals,
        model_family="Logistic Regression",
        methodology_note=(
            "Confidence is an algorithmic estimate based on observed corroborating evidence in the synthetic dataset. "
            "It does NOT represent proof, criminal probability, or guilt. Human verification required."
        )
    )

    # Resolve sanitized supporting records
    record_ids = edge_data.get("record_ids", [])
    supporting_records = _resolve_sanitized_records(
        record_ids=record_ids,
        source_id=actual_source,
        target_id=actual_target,
        case_id=edge_case_id
    )

    return EdgeProvenanceResponse(
        source_id=actual_source,
        source_label=s_label,
        source_type=s_type,
        target_id=actual_target,
        target_label=t_label,
        target_type=t_type,
        relationship_type=rel_type,
        case_id=edge_case_id,
        detection_method=det_method,
        confidence_breakdown=confidence_breakdown,
        supporting_records=supporting_records,
        safety_disclaimer=(
            "SYNTHETIC DEMONSTRATION DATA • Potential Relationship • "
            "Analytical lead only. Requires human verification. Does not determine guilt or criminality."
        )
    )
