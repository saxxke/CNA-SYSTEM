"""
validate_dataset.py
===================
Validates the rich synthetic dataset for:
  - File existence
  - Required columns
  - ID uniqueness
  - Foreign key integrity
  - Cross-case network scenarios (≥ 8 required)
  - Multi-case persons (at least 3 persons with ≥ 3 cases each)
  - Family relationship integrity

All data is SYNTHETIC DEMONSTRATION DATA.
"""

import os
import csv
from collections import defaultdict

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_TO_CHECK = [
    "cases.csv", "persons.csv", "phones.csv", "bank_accounts.csv",
    "vehicles.csv", "locations.csv", "organizations.csv",
    "aliases.csv", "families.csv", "case_persons.csv",
    "communications.csv", "transactions.csv", "ground_truth.csv",
]

REQUIRED_COLUMNS = {
    "cases.csv": ["case_id", "offence_category", "status", "district", "police_station"],
    "persons.csv": ["person_id", "full_name", "gender", "date_of_birth", "city",
                    "district", "phone_id", "bank_account_id"],
    "phones.csv": ["phone_id", "phone_number", "phone_type"],
    "bank_accounts.csv": ["bank_account_id", "account_number", "bank_name"],
    "vehicles.csv": ["vehicle_id", "registration_number", "vehicle_type"],
    "locations.csv": ["location_id", "city", "district", "state"],
    "organizations.csv": ["organization_id", "organization_name", "organization_type"],
    "aliases.csv": ["alias_id", "person_id", "alias_name"],
    "families.csv": ["family_id", "person_id", "related_person_id", "relationship_subtype"],
    "case_persons.csv": ["cp_id", "case_id", "person_id", "role"],
    "communications.csv": ["communication_id", "case_id", "source_person_id",
                           "target_person_id", "phone_id", "description"],
    "transactions.csv": ["transaction_id", "case_id", "source_person_id",
                         "target_person_id", "source_account_id", "target_account_id", "amount"],
    "ground_truth.csv": ["ground_truth_id", "source_entity_id", "target_entity_id",
                         "relationship_type", "expected_relationship"],
}

ID_COLUMNS = {
    "cases.csv":         "case_id",
    "persons.csv":       "person_id",
    "phones.csv":        "phone_id",
    "bank_accounts.csv": "bank_account_id",
    "vehicles.csv":      "vehicle_id",
    "locations.csv":     "location_id",
    "organizations.csv": "organization_id",
    "aliases.csv":       "alias_id",
    "families.csv":      "family_id",
    "case_persons.csv":  "cp_id",
    "communications.csv":"communication_id",
    "transactions.csv":  "transaction_id",
    "ground_truth.csv":  "ground_truth_id",
}


RUNTIME_DIR = os.path.join(DATA_DIR, "runtime")


def load_csv(filename, include_runtime=True):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        records = list(csv.DictReader(f))

    if include_runtime and os.path.exists(RUNTIME_DIR):
        runtime_filepath = os.path.join(RUNTIME_DIR, filename)
        if os.path.exists(runtime_filepath):
            with open(runtime_filepath, "r", encoding="utf-8") as rf:
                runtime_records = list(csv.DictReader(rf))
                records.extend(runtime_records)

    return records


def validate():
    print("RICH DATASET VALIDATION")
    print("=" * 50)
    all_pass = True

    # ── 1. FILE EXISTENCE ──────────────────────────────────────────────────
    all_data = {}
    print("\n[1] File Existence:")
    for fname in FILES_TO_CHECK:
        data = load_csv(fname, include_runtime=False)
        if data is None:
            print(f"  FAIL — {fname} missing")
            all_pass = False
        else:
            all_data[fname] = data
            print(f"  PASS — {fname}: {len(data)} rows")

    if not all_pass:
        print("Cannot continue — missing files.")
        return False

    # ── 2. REQUIRED COLUMNS ────────────────────────────────────────────────
    print("\n[2] Required Columns:")
    for fname, cols in REQUIRED_COLUMNS.items():
        if fname not in all_data or not all_data[fname]:
            continue
        row = all_data[fname][0]
        missing = [c for c in cols if c not in row]
        if missing:
            print(f"  FAIL — {fname} missing columns: {missing}")
            all_pass = False
        else:
            print(f"  PASS — {fname}")

    # ── 3. ID UNIQUENESS ───────────────────────────────────────────────────
    print("\n[3] ID Uniqueness:")
    entity_sets = {}
    for fname, id_col in ID_COLUMNS.items():
        if fname not in all_data:
            continue
        ids = [row[id_col] for row in all_data[fname] if row.get(id_col)]
        if len(ids) != len(set(ids)):
            dupes = [x for x in ids if ids.count(x) > 1]
            print(f"  FAIL — {fname} has duplicate {id_col}: {set(dupes)}")
            all_pass = False
        else:
            print(f"  PASS — {fname} ({len(ids)} unique IDs)")
        entity_sets[fname] = set(ids)

    # ── 4. FOREIGN KEY INTEGRITY ───────────────────────────────────────────
    print("\n[4] Foreign Key Integrity:")
    fk_pass = True

    person_ids   = entity_sets.get("persons.csv", set())
    case_ids     = entity_sets.get("cases.csv", set())
    phone_ids    = entity_sets.get("phones.csv", set())
    bank_ids     = entity_sets.get("bank_accounts.csv", set())
    vehicle_ids  = entity_sets.get("vehicles.csv", set())
    loc_ids      = entity_sets.get("locations.csv", set())
    org_ids      = entity_sets.get("organizations.csv", set())

    def fk_check(record, field, valid_set, context):
        nonlocal fk_pass
        val = record.get(field, "")
        if val and val not in valid_set:
            print(f"  FAIL FK — {context}: {field}={val} not found")
            fk_pass = False

    # persons → phones, banks, vehicles, locations, orgs
    for p in all_data["persons.csv"]:
        fk_check(p, "phone_id",        phone_ids,  "persons")
        fk_check(p, "phone_id_2",      phone_ids,  "persons")
        fk_check(p, "bank_account_id", bank_ids,   "persons")
        fk_check(p, "bank_account_id_2", bank_ids, "persons")
        fk_check(p, "vehicle_id",      vehicle_ids,"persons")
        fk_check(p, "vehicle_id_2",    vehicle_ids,"persons")
        fk_check(p, "location_id",     loc_ids,    "persons")
        fk_check(p, "organization_id", org_ids,    "persons")

    # aliases → persons
    for a in all_data["aliases.csv"]:
        fk_check(a, "person_id", person_ids, "aliases")

    # families → persons (both person_id and related_person_id)
    for f in all_data["families.csv"]:
        fk_check(f, "person_id",         person_ids, "families")
        fk_check(f, "related_person_id", person_ids, "families")

    # case_persons → cases, persons
    for cp in all_data["case_persons.csv"]:
        fk_check(cp, "case_id",   case_ids,   "case_persons")
        fk_check(cp, "person_id", person_ids, "case_persons")

    # communications → cases, persons, phones
    for c in all_data["communications.csv"]:
        fk_check(c, "case_id",          case_ids,   "communications")
        fk_check(c, "source_person_id", person_ids, "communications")
        fk_check(c, "target_person_id", person_ids, "communications")
        fk_check(c, "phone_id",         phone_ids,  "communications")

    # transactions → cases, persons, banks
    for t in all_data["transactions.csv"]:
        fk_check(t, "case_id",           case_ids,  "transactions")
        fk_check(t, "source_person_id",  person_ids,"transactions")
        fk_check(t, "target_person_id",  person_ids,"transactions")
        fk_check(t, "source_account_id", bank_ids,  "transactions")
        fk_check(t, "target_account_id", bank_ids,  "transactions")

    if fk_pass:
        print("  PASS — All foreign keys valid")
    else:
        all_pass = False

    # ── 5. CROSS-CASE NETWORK SCENARIOS ───────────────────────────────────
    print("\n[5] Cross-Case Network Scenarios:")
    person_cases = defaultdict(set)
    for cp in all_data["case_persons.csv"]:
        if cp.get("case_id") and cp.get("person_id"):
            person_cases[cp["person_id"]].add(cp["case_id"])
    for c in all_data["communications.csv"]:
        if c.get("case_id"):
            person_cases[c.get("source_person_id","")].add(c["case_id"])
            person_cases[c.get("target_person_id","")].add(c["case_id"])
    for t in all_data["transactions.csv"]:
        if t.get("case_id"):
            person_cases[t.get("source_person_id","")].add(t["case_id"])
            person_cases[t.get("target_person_id","")].add(t["case_id"])

    cross_case = 0
    for c in all_data["communications.csv"]:
        p1, p2 = c.get("source_person_id",""), c.get("target_person_id","")
        if person_cases[p1] | person_cases[p2]:
            combined = person_cases[p1] | person_cases[p2]
            if len(combined) > 1:
                cross_case += 1
    for t in all_data["transactions.csv"]:
        p1, p2 = t.get("source_person_id",""), t.get("target_person_id","")
        combined = person_cases[p1] | person_cases[p2]
        if len(combined) > 1:
            cross_case += 1

    if cross_case >= 8:
        print(f"  PASS - {cross_case} cross-case connections detected (min 8)")
    else:
        print(f"  FAIL - Only {cross_case} cross-case connections (need >= 8)")
        all_pass = False

    # -- 6. MULTI-CASE PERSONS ---------------------------------------------
    print("\n[6] Multi-Case Persons:")
    multi_case = [(pid, len(cases)) for pid, cases in person_cases.items() if len(cases) >= 3]
    multi_case.sort(key=lambda x: -x[1])
    if len(multi_case) >= 3:
        print(f"  PASS - {len(multi_case)} persons with >= 3 associated cases")
        for pid, cnt in multi_case[:5]:
            print(f"         {pid}: {cnt} cases")
    else:
        print(f"  FAIL - Only {len(multi_case)} persons with >= 3 cases (need >= 3)")
        all_pass = False

    # -- 7. FAMILY RELATIONSHIP INTEGRITY ----------------------------------
    print("\n[7] Family Relationships:")
    family_subtypes = {f["relationship_subtype"] for f in all_data["families.csv"]}
    required_subtypes = {"FATHER", "MOTHER", "SPOUSE", "BROTHER", "SISTER", "CHILD"}
    missing_subtypes = required_subtypes - family_subtypes
    if missing_subtypes:
        print(f"  WARN - Missing subtypes: {missing_subtypes} (not a hard failure)")
    else:
        print(f"  PASS - All required family subtypes present: {family_subtypes}")
    print(f"  INFO - Total family records: {len(all_data['families.csv'])}")

    # -- 8. GROUND TRUTH QUALITY -------------------------------------------
    print("\n[8] Ground Truth Quality:")
    gt = all_data["ground_truth.csv"]
    positives = [g for g in gt if g.get("expected_relationship") == "1"]
    negatives = [g for g in gt if g.get("expected_relationship") == "0"]
    if len(positives) >= 10 and len(negatives) >= 10:
        print(f"  PASS - {len(positives)} positive, {len(negatives)} negative examples")
    else:
        print(f"  FAIL - Insufficient GT: {len(positives)} pos, {len(negatives)} neg")
        all_pass = False

    # -- 9. DUPLICATE ER TEST CASES ----------------------------------------
    print("\n[9] Entity Resolution Test Cases:")
    phone_variants = any("-V" in p["phone_id"] for p in all_data["phones.csv"])
    vehicle_variants = any("-V" in v["vehicle_id"] for v in all_data["vehicles.csv"])
    bank_variants = any("-V" in b["bank_account_id"] for b in all_data["bank_accounts.csv"])
    alias_count = len(all_data["aliases.csv"])
    if phone_variants and vehicle_variants and bank_variants and alias_count > 0:
        print(f"  PASS - Phone, vehicle, bank variants + {alias_count} aliases for ER testing")
    else:
        print("  WARN - Some ER test cases missing")

    # -- 10. NLP READINESS -------------------------------------------------
    print("\n[10] NLP Readiness (Human-readable descriptions):")
    comms = all_data["communications.csv"]
    human_readable = sum(1 for c in comms
                         if any(p["full_name"].split()[0] in c.get("description","")
                                for p in all_data["persons.csv"][:31]))
    print(f"  INFO - {human_readable}/{len(comms)} communications contain recognizable person names")
    if human_readable >= 10:
        print("  PASS - Sufficient human-readable communication records for NLP pipeline")
    else:
        print("  WARN - Few human-readable communications detected")

    # -- SUMMARY -----------------------------------------------------------
    print("\n" + "=" * 50)
    if all_pass:
        print("OVERALL: PASS - Dataset is valid and ready for pipeline integration.")
    else:
        print("OVERALL: FAIL - See above failures before proceeding.")
    return all_pass


if __name__ == "__main__":
    success = validate()
    import sys
    sys.exit(0 if success else 1)
