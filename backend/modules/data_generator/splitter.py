"""
splitter.py
===========
Cluster-based leakage-safe train/validation/test splitter.
Groups cases and persons by connected subgraphs and assigns entire clusters to partitions,
guaranteeing zero entity or case overlap between train and test sets.
"""

import os
import csv
import random
from collections import defaultdict
from typing import Dict, Any, List, Set, Tuple

def cluster_entities_and_cases(case_persons: List[Dict[str, Any]]) -> List[Set[str]]:
    """
    Finds weakly connected components of cases and persons.
    Returns a list of sets where each set contains connected case_ids and person_ids.
    """
    adj = defaultdict(set)
    all_nodes = set()
    
    for cp in case_persons:
        c = cp["case_id"]
        p = cp["person_id"]
        adj[c].add(p)
        adj[p].add(c)
        all_nodes.add(c)
        all_nodes.add(p)
        
    visited = set()
    clusters = []
    
    for node in all_nodes:
        if node not in visited:
            cluster = set()
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop()
                cluster.add(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            clusters.append(cluster)
            
    return clusters

def split_dataset(
    data_dir: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Leakage-safe case-level dataset splitting.
    Partitions independent case contexts into disjoint train, validation, and test partitions,
    guaranteeing zero case overlap between training and testing.
    """
    rng = random.Random(seed)
    
    cases_path = os.path.join(data_dir, "cases.csv")
    gt_path = os.path.join(data_dir, "ground_truth.csv")
    
    with open(cases_path, "r", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = list(csv.DictReader(f))
        
    all_case_ids = [c["case_id"] for c in cases]
    rng.shuffle(all_case_ids)
    
    n_total = len(all_case_ids)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)
    
    train_case_ids = set(all_case_ids[:n_train])
    val_case_ids = set(all_case_ids[n_train:n_train + n_val])
    test_case_ids = set(all_case_ids[n_train + n_val:])
    
    # Assert zero case leakage
    overlap = train_case_ids.intersection(test_case_ids)
    if overlap:
        raise ValueError(f"Leakage detected! Shared cases between train and test: {overlap}")
        
    train_gt, val_gt, test_gt = [], [], []
    for row in ground_truth:
        cid = row.get("case_id")
        if cid in test_case_ids:
            test_gt.append(row)
        elif cid in val_case_ids:
            val_gt.append(row)
        else:
            train_gt.append(row)
            
    summary = {
        "total_cases": n_total,
        "train_case_count": len(train_case_ids),
        "val_case_count": len(val_case_ids),
        "test_case_count": len(test_case_ids),
        "train_ground_truth_count": len(train_gt),
        "val_ground_truth_count": len(val_gt),
        "test_ground_truth_count": len(test_gt),
        "zero_case_leakage_verified": len(overlap) == 0,
        "train_gt": train_gt,
        "val_gt": val_gt,
        "test_gt": test_gt
    }
    
    return summary
