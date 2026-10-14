"""
generator.py
============
Orchestrator for generating reproducible synthetic investigation datasets.
Preserves schema, unique IDs, and outputs clean CSVs paired with metadata.json.
"""

import os
import csv
import json
import random
import time
from typing import Dict, Any, Optional

from modules.data_generator.config import PROFILES
from modules.data_generator.entity_factories import EntityFactories
from modules.data_generator.scenario_builder import build_scenarios
from modules.data_generator.validator import validate_dataset_directory

def write_table_csv(filepath: str, rows: list, fieldnames: list):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def generate_dataset(
    profile: str = "SMALL",
    output_dir: Optional[str] = None,
    seed: int = 42
) -> Dict[str, Any]:
    start_time = time.time()
    
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}. Supported: {list(PROFILES.keys())}")
        
    cfg = PROFILES[profile]
    
    if output_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/expanded"))
        output_dir = os.path.join(base_dir, profile.lower())
        
    os.makedirs(output_dir, exist_ok=True)
    
    rng = random.Random(seed)
    factories = EntityFactories(rng)
    
    # 1. Base Entities
    locations = factories.create_locations(cfg["locations"])
    phones = factories.create_phones(cfg["phones"])
    bank_accounts = factories.create_bank_accounts(cfg["bank_accounts"])
    vehicles = factories.create_vehicles(cfg["vehicles"])
    organizations = factories.create_organizations(cfg["organizations"])
    persons = factories.create_persons(cfg["persons"], phones, bank_accounts)
    cases = factories.create_cases(cfg["cases"])
    
    # 2. Relational Topologies & Scenarios
    scenarios = build_scenarios(
        factories=factories,
        persons=persons,
        cases=cases,
        phones=phones,
        bank_accounts=bank_accounts,
        profile_cfg=cfg,
        rng=rng
    )
    
    case_persons = scenarios["case_persons"]
    aliases = scenarios["aliases"]
    families = scenarios["families"]
    communications = scenarios["communications"]
    transactions = scenarios["transactions"]
    ground_truth = scenarios["ground_truth"]
    
    # 3. Write All 13 Standard CSV Files (Clean CSV format, Zero comment lines)
    tables = {
        "cases.csv": (cases, ["case_id", "fir_number", "offence_category", "title", "legal_section", "year", "location", "district", "police_station", "status"]),
        "persons.csv": (persons, ["person_id", "full_name", "gender", "date_of_birth", "age", "occupation", "city", "district", "phone_id", "bank_account_id"]),
        "case_persons.csv": (case_persons, ["cp_id", "case_id", "person_id", "role", "narrative"]),
        "phones.csv": (phones, ["phone_id", "phone_number", "phone_type", "imei", "service_provider"]),
        "bank_accounts.csv": (bank_accounts, ["bank_account_id", "account_number", "bank_name", "ifsc_code", "branch"]),
        "vehicles.csv": (vehicles, ["vehicle_id", "registration_number", "vehicle_type", "model", "color"]),
        "locations.csv": (locations, ["location_id", "city", "district", "state", "pincode", "police_station"]),
        "organizations.csv": (organizations, ["organization_id", "organization_name", "organization_type", "registration_number"]),
        "aliases.csv": (aliases, ["alias_id", "person_id", "alias_name", "context"]),
        "families.csv": (families, ["family_id", "person_id", "related_person_id", "relationship_subtype"]),
        "communications.csv": (communications, ["communication_id", "case_id", "source_person_id", "target_person_id", "phone_id", "communication_type", "description"]),
        "transactions.csv": (transactions, ["transaction_id", "case_id", "source_person_id", "target_person_id", "source_account_id", "target_account_id", "amount", "description"]),
        "ground_truth.csv": (ground_truth, ["ground_truth_id", "source_entity_id", "target_entity_id", "relationship_type", "expected_relationship", "case_id", "evidence_reference"]),
    }
    
    record_counts = {}
    for fname, (rows, fnames) in tables.items():
        fpath = os.path.join(output_dir, fname)
        write_table_csv(fpath, rows, fnames)
        record_counts[fname] = len(rows)
        
    duration = round(time.time() - start_time, 3)
    
    # 4. Write metadata.json (Disclaimers, Counts, Seed, Timestamps)
    metadata = {
        "profile": profile,
        "seed": seed,
        "generation_time_seconds": duration,
        "disclaimer": "SYNTHETIC DEMONSTRATION DATA. Fully fictional investigation records generated for model training and benchmarking. Does not represent real persons, cases, or surveillance data.",
        "record_counts": record_counts
    }
    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    # 5. Write README.md
    readme_content = f"""# Synthetic Investigation Dataset — Profile: {profile}

> **SYNTHETIC DEMONSTRATION DATA ONLY**
> All records in this directory are 100% fictional and synthetically generated for machine learning training, topological graph stress-testing, and analytical validation.
> No real phone numbers, bank accounts, home addresses, or police records are used.

## Generation Metadata
- **Profile**: {profile}
- **Seed**: {seed}
- **Generation Time**: {duration}s
- **Total Persons**: {len(persons)}
- **Total Cases**: {len(cases)}
- **Case-Person Associations**: {len(case_persons)}
- **Ground Truth Pairs**: {len(ground_truth)}
"""
    with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    # 6. Validate generated directory
    val_res = validate_dataset_directory(output_dir)
    if not val_res["valid"]:
        raise ValueError(f"Generated dataset validation failed: {val_res['errors']}")
        
    return {
        "profile": profile,
        "seed": seed,
        "output_dir": output_dir,
        "generation_time": duration,
        "record_counts": record_counts,
        "validation": val_res
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic investigation datasets")
    parser.add_argument("--profile", default="SMALL", choices=["SMALL", "MEDIUM", "LARGE"], help="Dataset scale profile")
    parser.add_argument("--seed", type=int, default=42, help="Pseudorandom integer seed")
    parser.add_argument("--output", default=None, help="Target output directory")
    args = parser.parse_args()
    
    res = generate_dataset(profile=args.profile, output_dir=args.output, seed=args.seed)
    print(f"Generated {args.profile} dataset in {res['generation_time']}s at {res['output_dir']}")
    print(json.dumps(res["record_counts"], indent=2))
