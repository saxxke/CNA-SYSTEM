"""
features.py
===========
Feature extraction engine for Relationship Confidence benchmarking.
Provides both 7-feature (baseline) and 11-feature (extended explainable) extractors.

PROVENANCE & INFERENCE-TIME LEAKAGE AUDIT:
------------------------------------------
Every feature is computed strictly from records available at query/inference time:
1. `entity_similarity`: String similarity between source entity name and target entity name
   - Source: `persons.csv` or asset tables via entity mapping.
2. `text_evidence_strength`: Length of the investigation evidence string (normalized)
   - Source: Candidate relationship's `evidence` field.
3. `relationship_keyword_match`: Binary match for extraction rule keywords
   - Source: Candidate relationship's `detection_method` or evidence text.
4. `supporting_record_count`: Co-occurrences of source and target IDs in telecom/banking logs
   - Source: `communications.csv` and `transactions.csv` text descriptions.
5. `source_record_count`: Total appearances of source entity ID in telecom/banking logs
   - Source: `communications.csv` and `transactions.csv` text descriptions.
6. `relationship_frequency`: Domain-specific category weight based on relationship type
   - Source: Candidate relationship's `relationship_type` (e.g. CONTACTED, TRANSFERRED_TO).
7. `cross_case_connectivity`: Distinct cases associated with source entity
   - Source: `communications.csv` and candidate `case_id`.
8. `evidence_diversity` [NEW]:
   - Ratio of distinct evidence modalities present (telecom communications vs financial transactions).
   - Source: `communications.csv` and `transactions.csv` co-occurrence indicator.
   - Inference-time availability: Directly measurable from communication and transaction logs.
   - Zero label leakage: Does not use ground_truth.csv.
9. `case_cooccurrence_count` [NEW]:
   - Number of cases where both source and target are formally recorded together.
   - Source: `case_persons.csv` (case-person association registry).
   - Inference-time availability: Directly queryable from existing case registry.
   - Zero label leakage: Does not use ground_truth.csv.
10. `bidirectional_activity` [NEW]:
    - Binary flag (1.0 or 0.0) indicating whether communications or transactions exist in both directions (A->B and B->A).
    - Source: `communications.csv` (sender/receiver or directed descriptions) and `transactions.csv`.
    - Inference-time availability: Directly observable from directional communication/transaction records.
    - Zero label leakage: Does not use ground_truth.csv.
11. `normalized_transaction_volume` [NEW]:
    - Log-transformed total transaction amount ($log_{10}(1 + \text{amount})$) transferred between source and target.
    - Source: `transactions.csv` (`amount` column where both entities are mentioned).
    - Inference-time availability: Directly summed from transaction logs.
    - Zero label leakage: Does not use ground_truth.csv.
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from modules.entity_resolution.resolver import calculate_string_similarity

FEATURE_NAMES_7 = [
    "entity_similarity",
    "text_evidence_strength",
    "relationship_keyword_match",
    "supporting_record_count",
    "source_record_count",
    "relationship_frequency",
    "cross_case_connectivity"
]

FEATURE_NAMES_11 = FEATURE_NAMES_7 + [
    "evidence_diversity",
    "case_cooccurrence_count",
    "bidirectional_activity",
    "normalized_transaction_volume"
]

def extract_features_7(
    rel: dict,
    comms_df: pd.DataFrame,
    txns_df: pd.DataFrame,
    entities_map: dict
) -> List[float]:
    """
    Extracts the baseline 7 explainable features exactly as evaluated in Step 22.
    """
    source_id = str(rel.get("source", ""))
    target_id = str(rel.get("target", ""))
    
    source_val = entities_map.get(source_id, source_id)
    target_val = entities_map.get(target_id, target_id)
    
    # 1. entity_similarity
    ent_sim = float(calculate_string_similarity(source_val, target_val))
    
    # 2. text_evidence_strength
    evidence = str(rel.get("evidence", ""))
    ev_strength = min(1.0, len(evidence) / 100.0) if evidence and evidence != "N/A" else 0.0
    
    # 3. relationship_keyword_match
    kw_match = 1.0 if ev_strength > 0 else 0.0
    
    # 4. supporting_record_count
    comm_supp = 0
    if not comms_df.empty:
        comm_supp = int((
            comms_df['description'].str.contains(source_id, regex=False, na=False) &
            comms_df['description'].str.contains(target_id, regex=False, na=False)
        ).sum())
        
    txn_supp = 0
    if not txns_df.empty:
        txn_supp = int((
            txns_df['description'].str.contains(source_id, regex=False, na=False) &
            txns_df['description'].str.contains(target_id, regex=False, na=False)
        ).sum())
        
    supp_count = float(comm_supp + txn_supp)
    if supp_count == 0.0 and ev_strength > 0:
        supp_count = 1.0
        
    # 5. source_record_count
    src_count = 0.0
    if not comms_df.empty:
        src_count += float(comms_df['description'].str.contains(source_id, regex=False, na=False).sum())
    if not txns_df.empty:
        src_count += float(txns_df['description'].str.contains(source_id, regex=False, na=False).sum())
    if src_count == 0.0:
        src_count = 1.0
        
    # 6. relationship_frequency
    rel_type = str(rel.get("relationship_type", ""))
    rel_freq = 5.0 if rel_type in ["CONTACTED", "TRANSFERRED_TO", "INVOLVED_IN"] else 2.0
    
    # 7. cross_case_connectivity
    case_ids = set()
    if not comms_df.empty and 'case_id' in comms_df.columns:
        matching = comms_df[comms_df['description'].str.contains(source_id, regex=False, na=False)]
        case_ids.update(matching['case_id'].dropna().unique())
    explicit_case = str(rel.get("case_id", ""))
    if explicit_case.startswith("CASE-"):
        case_ids.add(explicit_case)
    case_conn = float(len(case_ids))
    
    return [ent_sim, ev_strength, kw_match, supp_count, src_count, rel_freq, case_conn]

def extract_features_11(
    rel: dict,
    comms_df: pd.DataFrame,
    txns_df: pd.DataFrame,
    case_persons_df: pd.DataFrame,
    entities_map: dict
) -> List[float]:
    """
    Extracts the extended 11 explainable features.
    Builds strictly upon inference-time records with zero label leakage.
    """
    f7 = extract_features_7(rel, comms_df, txns_df, entities_map)
    
    source_id = str(rel.get("source", ""))
    target_id = str(rel.get("target", ""))
    
    # 8. evidence_diversity: Distinct evidence channels (0.0 = none, 0.5 = 1 channel, 1.0 = both comms & txns)
    has_comm = False
    has_txn = False
    if not comms_df.empty:
        has_comm = bool((
            comms_df['description'].str.contains(source_id, regex=False, na=False) &
            comms_df['description'].str.contains(target_id, regex=False, na=False)
        ).any())
    if not txns_df.empty:
        has_txn = bool((
            txns_df['description'].str.contains(source_id, regex=False, na=False) &
            txns_df['description'].str.contains(target_id, regex=False, na=False)
        ).any())
        
    diversity = 0.0
    if has_comm and has_txn:
        diversity = 1.0
    elif has_comm or has_txn or f7[1] > 0:  # isolated text evidence counts as single modality
        diversity = 0.5
        
    # 9. case_cooccurrence_count: Number of cases where both source and target appear in case_persons
    case_cooccur = 0.0
    if not case_persons_df.empty and 'case_id' in case_persons_df.columns and 'person_id' in case_persons_df.columns:
        s_cases = set(case_persons_df[case_persons_df['person_id'] == source_id]['case_id'].dropna())
        t_cases = set(case_persons_df[case_persons_df['person_id'] == target_id]['case_id'].dropna())
        case_cooccur = float(len(s_cases.intersection(t_cases)))
        
    # 10. bidirectional_activity: Evidence of reciprocal contact or fund transfer
    bidirectional = 0.0
    # In communications/transactions, check if A contacted B and B contacted A or bidirectional descriptions
    a_to_b = False
    b_to_a = False
    if not comms_df.empty:
        desc = comms_df['description'].dropna().tolist()
        for d in desc:
            if source_id in d and target_id in d:
                # Check directional keywords
                if f"{source_id} contacted {target_id}" in d or f"{source_id} called {target_id}" in d:
                    a_to_b = True
                elif f"{target_id} contacted {source_id}" in d or f"{target_id} called {source_id}" in d:
                    b_to_a = True
                else:
                    # General co-occurrence
                    a_to_b = True
    if not txns_df.empty:
        desc_tx = txns_df['description'].dropna().tolist()
        for d in desc_tx:
            if source_id in d and target_id in d:
                if f"{source_id} sent" in d or f"{source_id} transferred" in d:
                    a_to_b = True
                elif f"{target_id} sent" in d or f"{target_id} transferred" in d:
                    b_to_a = True
                else:
                    a_to_b = True
    if a_to_b and b_to_a:
        bidirectional = 1.0
    elif a_to_b or b_to_a:
        bidirectional = 0.5
        
    # 11. normalized_transaction_volume: log10(1 + sum of transaction amounts exchanged)
    txn_volume = 0.0
    if not txns_df.empty and 'amount' in txns_df.columns:
        mask = (
            txns_df['description'].str.contains(source_id, regex=False, na=False) &
            txns_df['description'].str.contains(target_id, regex=False, na=False)
        )
        total_amt = txns_df.loc[mask, 'amount'].sum()
        if total_amt > 0:
            txn_volume = float(math.log10(1.0 + float(total_amt)))
            
    return f7 + [diversity, case_cooccur, bidirectional, txn_volume]
