"""
test_data_validation.py
=======================
Automated test suite for Member 2 Data Engineering and Validation responsibilities.

Tests:
1. Valid baseline dataset passes all schema, ID, FK, and semantic checks
2. Detection of missing primary keys (empty or whitespace IDs)
3. Detection of duplicate primary key identifiers
4. Detection of broken foreign key referential links
5. Detection of invalid record fields (malformed dates, invalid enums, negative amounts)
6. Duplicate FIR number detection
7. Runtime store pre-commit validation rejects invalid, duplicate, or broken records
8. Source provenance identifiers (cp_id, communication_id, transaction_id, etc.) are preserved
9. Runtime data isolation from baseline demo data
"""

import os
import sys
import copy
import tempfile
import shutil

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import pytest
except ImportError:
    pytest = None

from data.validate_dataset import (
    validate_dataset,
    validate_single_record,
    load_csv,
    FILES_TO_CHECK
)
from modules.persistence.runtime_store import (
    append_runtime_record,
    clear_runtime_data,
    validate_runtime_record,
    get_all_records,
    get_runtime_records,
    get_baseline_records,
    get_next_case_id,
    get_next_person_id,
    get_next_cp_id,
    RUNTIME_DIR
)


_RUNTIME_BACKUP = {}

def setup_clean_runtime():
    global _RUNTIME_BACKUP
    _RUNTIME_BACKUP = {}
    if os.path.exists(RUNTIME_DIR):
        for fname in os.listdir(RUNTIME_DIR):
            fpath = os.path.join(RUNTIME_DIR, fname)
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    _RUNTIME_BACKUP[fname] = f.read()
    clear_runtime_data()


def teardown_clean_runtime():
    clear_runtime_data()
    global _RUNTIME_BACKUP
    for fname, content in _RUNTIME_BACKUP.items():
        fpath = os.path.join(RUNTIME_DIR, fname)
        with open(fpath, "wb") as f:
            f.write(content)


def test_1_baseline_dataset_passes_validation():
    """Requirement: The baseline synthetic dataset must pass 100% of validation checks."""
    res = validate_dataset(include_runtime=False)
    assert res["valid"] is True, f"Baseline validation failed: {res['errors']}"
    assert len(res["errors"]) == 0
    assert res["metrics"]["total_cases"] >= 250
    assert res["metrics"]["total_persons"] >= 200


def test_2_missing_primary_key_detected():
    """Requirement: Validator must catch missing/empty primary key values."""
    # Test on a single record
    record = {
        "case_id": "   ",  # Blank whitespace ID
        "offence_category": "Fraud",
        "status": "OPEN",
        "district": "Raipur",
        "police_station": "Civil Lines"
    }
    is_valid, errors = validate_single_record("cases.csv", record)
    assert is_valid is False
    assert any("primary key" in err.lower() for err in errors)


def test_3_duplicate_primary_key_detected():
    """Requirement: Validator must flag duplicate primary keys."""
    # Person with existing ID PERSON-001
    cache = {"persons.csv": {"PERSON-001", "PERSON-002"}}
    record = {
        "person_id": "PERSON-001",
        "full_name": "Duplicate Subject",
        "gender": "MALE",
        "district": "Raipur"
    }
    is_valid, errors = validate_single_record("persons.csv", record, valid_ids_cache=cache)
    assert is_valid is False
    assert any("duplicate primary key" in err.lower() for err in errors)


def test_4_broken_foreign_key_detected():
    """Requirement: Validator must detect broken foreign key references."""
    cache = {
        "cases.csv": {"CASE-001"},
        "persons.csv": {"PERSON-001"}
    }
    record = {
        "cp_id": "CP-CASE-999-PERSON-999",
        "case_id": "CASE-999",  # Broken FK
        "person_id": "PERSON-001",
        "role": "SUSPECT"
    }
    is_valid, errors = validate_single_record("case_persons.csv", record, valid_ids_cache=cache)
    assert is_valid is False
    assert any("foreign key reference broken" in err.lower() for err in errors)


def test_5_invalid_date_format_detected():
    """Requirement: Validator must catch non-conforming date strings."""
    record = {
        "case_id": "CASE-900",
        "offence_category": "Extortion",
        "status": "OPEN",
        "date_opened": "14/10/2026",  # Invalid format (should be YYYY-MM-DD)
        "district": "Raipur",
        "police_station": "City Kotwali"
    }
    is_valid, errors = validate_single_record("cases.csv", record)
    assert is_valid is False
    assert any("date_opened" in err for err in errors)


def test_6_invalid_case_status_enum_detected():
    """Requirement: Validator must reject unknown case status enums."""
    record = {
        "case_id": "CASE-901",
        "offence_category": "Extortion",
        "status": "INVALID_PENDING",  # Disallowed status
        "district": "Raipur",
        "police_station": "City Kotwali"
    }
    is_valid, errors = validate_single_record("cases.csv", record)
    assert is_valid is False
    assert any("status" in err.lower() for err in errors)


def test_6b_duplicate_fir_detected():
    """Requirement: Validator must catch duplicate FIR numbers."""
    # FIR-SYNTH-RAI-0001 already exists in baseline CASE-001
    bad_case = {
        "case_id": "CASE-902",
        "offence_category": "Extortion",
        "status": "OPEN",
        "fir_number": "FIR-SYNTH-RAI-0001",
        "district": "Raipur",
        "police_station": "Civil Lines"
    }
    is_valid, errors = validate_runtime_record("cases.csv", bad_case)
    assert is_valid is False
    assert any("duplicate fir" in err.lower() for err in errors)


def test_7_negative_transaction_amount_detected():
    """Requirement: Validator must reject non-positive or negative transaction amounts."""
    record = {
        "transaction_id": "TXN-999",
        "case_id": "CASE-001",
        "source_person_id": "PERSON-001",
        "target_person_id": "PERSON-002",
        "amount": "-5000"  # Negative amount
    }
    is_valid, errors = validate_single_record("transactions.csv", record)
    assert is_valid is False
    assert any("positive" in err.lower() for err in errors)


def test_8_runtime_pre_commit_validation_enforced():
    """Requirement: runtime_store must block invalid records from being appended."""
    setup_clean_runtime()
    try:
        # Attempt to append record with missing primary key
        bad_case = {
            "case_id": "",
            "case_title": "Bad Incident",
            "offence_category": "Theft",
            "status": "OPEN"
        }
        try:
            append_runtime_record("cases.csv", bad_case)
            assert False, "Should have raised ValueError on missing primary key"
        except ValueError as e:
            assert "primary key" in str(e).lower()

        # Attempt to append case_persons with broken reference
        bad_cp = {
            "cp_id": "CPA-9999",
            "case_id": "CASE-NONEXISTENT-999",
            "person_id": "PERSON-NONEXISTENT-999",
            "role": "SUSPECT"
        }
        try:
            append_runtime_record("case_persons.csv", bad_cp)
            assert False, "Should have raised ValueError on broken foreign key"
        except ValueError as e:
            assert "non-existent" in str(e).lower()

        # Valid append succeeds
        cid = get_next_case_id()
        valid_case = {
            "case_id": cid,
            "case_title": "Valid Incident",
            "offence_category": "Theft",
            "status": "OPEN",
            "fir_number": "FIR-SYNTH-TEST-VALID-01",
            "district": "Raipur",
            "police_station": "Civil Lines"
        }
        append_runtime_record("cases.csv", valid_case)
        runtime_cases = get_runtime_records("cases.csv")
        assert len(runtime_cases) == 1
        assert runtime_cases[0]["case_id"] == cid

    finally:
        teardown_clean_runtime()


def test_9_provenance_identifiers_preserved():
    """Requirement: All analytical records must have non-empty provenance identifiers."""
    cps = load_csv("case_persons.csv", include_runtime=False)
    for cp in cps:
        assert cp.get("cp_id"), "Missing cp_id provenance key"
        assert cp["case_id"] and cp["person_id"]

    comms = load_csv("communications.csv", include_runtime=False)
    for c in comms:
        assert c.get("communication_id"), "Missing communication_id provenance key"

    txns = load_csv("transactions.csv", include_runtime=False)
    for t in txns:
        assert t.get("transaction_id"), "Missing transaction_id provenance key"

    gt = load_csv("ground_truth.csv", include_runtime=False)
    for g in gt:
        assert g.get("ground_truth_id"), "Missing ground_truth_id provenance key"


def test_10_runtime_data_isolation_preserved():
    """Requirement: Runtime records must never leak into or alter baseline backend/data/*.csv files."""
    setup_clean_runtime()
    try:
        baseline_cases_before = get_baseline_records("cases.csv")
        count_before = len(baseline_cases_before)

        # Append runtime case
        cid = get_next_case_id()
        append_runtime_record("cases.csv", {
            "case_id": cid,
            "case_title": "Isolated Runtime Case",
            "offence_category": "Cybercrime",
            "status": "OPEN",
            "fir_number": "FIR-SYNTH-ISOLATED-01",
            "district": "Kolkata",
            "police_station": "Park Street"
        })

        baseline_cases_after = get_baseline_records("cases.csv")
        assert len(baseline_cases_after) == count_before, "Baseline file was altered by runtime append!"

        combined = get_all_records("cases.csv")
        assert len(combined) == count_before + 1
        assert any(c["case_id"] == cid for c in combined)

    finally:
        teardown_clean_runtime()


if __name__ == "__main__":
    print("=" * 60)
    print("Running Member 2 Data Validation Test Suite")
    print("=" * 60)
    test_1_baseline_dataset_passes_validation()
    print("  PASS - test_1_baseline_dataset_passes_validation")
    test_2_missing_primary_key_detected()
    print("  PASS - test_2_missing_primary_key_detected")
    test_3_duplicate_primary_key_detected()
    print("  PASS - test_3_duplicate_primary_key_detected")
    test_4_broken_foreign_key_detected()
    print("  PASS - test_4_broken_foreign_key_detected")
    test_5_invalid_date_format_detected()
    print("  PASS - test_5_invalid_date_format_detected")
    test_6_invalid_case_status_enum_detected()
    print("  PASS - test_6_invalid_case_status_enum_detected")
    test_6b_duplicate_fir_detected()
    print("  PASS - test_6b_duplicate_fir_detected")
    test_7_negative_transaction_amount_detected()
    print("  PASS - test_7_negative_transaction_amount_detected")
    test_8_runtime_pre_commit_validation_enforced()
    print("  PASS - test_8_runtime_pre_commit_validation_enforced")
    test_9_provenance_identifiers_preserved()
    print("  PASS - test_9_provenance_identifiers_preserved")
    test_10_runtime_data_isolation_preserved()
    print("  PASS - test_10_runtime_data_isolation_preserved")
    print("=" * 60)
    print("ALL 11 DATA VALIDATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
