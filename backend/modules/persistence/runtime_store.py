"""
runtime_store.py
================
Isolated runtime persistence layer for Step 27 Register New Case + Person.
Preserves baseline backend/data/*.csv files byte-for-byte.
All mutations are stored in backend/data/runtime/*.csv.
Thread-safe deterministic ID allocation inspecting baseline + runtime records.
Includes pre-commit schema and referential integrity validation.
"""

import os
import csv
import re
import threading
from typing import Dict, List, Any, Optional, Tuple, Set

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
RUNTIME_DIR = os.path.join(DATA_DIR, 'runtime')

_STORE_LOCK = threading.Lock()

# Standardized headers for runtime tables
SCHEMAS = {
    "cases.csv": [
        "case_id", "case_title", "offence_category", "legal_section", "fir_number",
        "date_opened", "description", "status", "police_station", "district", "state",
        "location_id", "created_at", "created_by"
    ],
    "persons.csv": [
        "person_id", "full_name", "first_name", "last_name", "gender", "date_of_birth",
        "age", "occupation", "education", "address", "locality", "city", "district",
        "state", "pin_code", "phone_id", "phone_id_2", "bank_account_id",
        "bank_account_id_2", "vehicle_id", "vehicle_id_2", "location_id",
        "organization_id", "email", "created_at", "created_by"
    ],
    "case_persons.csv": [
        "cp_id", "case_id", "person_id", "association", "role", "source",
        "created_at", "created_by"
    ],
    "phones.csv": [
        "phone_id", "phone_number", "phone_type", "created_at", "created_by"
    ],
    "bank_accounts.csv": [
        "bank_account_id", "account_number", "bank_name", "created_at", "created_by"
    ],
    "vehicles.csv": [
        "vehicle_id", "registration_number", "vehicle_type", "created_at", "created_by"
    ],
    "locations.csv": [
        "location_id", "city", "district", "state", "locality", "created_at", "created_by"
    ],
    "organizations.csv": [
        "organization_id", "organization_name", "organization_type", "created_at", "created_by"
    ],
    "aliases.csv": [
        "alias_id", "person_id", "alias_name", "created_at", "created_by"
    ],
    "communications.csv": [
        "communication_id", "case_id", "source_person_id", "target_person_id",
        "phone_id", "description", "created_at", "created_by"
    ],
    "transactions.csv": [
        "transaction_id", "case_id", "source_person_id", "target_person_id",
        "source_account_id", "target_account_id", "amount", "created_at", "created_by"
    ],
}

ID_COLUMNS = {
    "cases.csv": "case_id",
    "persons.csv": "person_id",
    "phones.csv": "phone_id",
    "bank_accounts.csv": "bank_account_id",
    "vehicles.csv": "vehicle_id",
    "locations.csv": "location_id",
    "organizations.csv": "organization_id",
    "aliases.csv": "alias_id",
    "case_persons.csv": "cp_id",
    "communications.csv": "communication_id",
    "transactions.csv": "transaction_id",
}


def ensure_runtime_dir():
    """Ensures backend/data/runtime directory exists."""
    os.makedirs(RUNTIME_DIR, exist_ok=True)


def get_baseline_records(filename: str) -> List[Dict[str, Any]]:
    """Reads baseline records from backend/data/<filename>."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_runtime_records(filename: str) -> List[Dict[str, Any]]:
    """Reads runtime records from backend/data/runtime/<filename>."""
    filepath = os.path.join(RUNTIME_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_all_records(filename: str) -> List[Dict[str, Any]]:
    """Returns combined baseline + runtime records."""
    baseline = get_baseline_records(filename)
    runtime = get_runtime_records(filename)
    return baseline + runtime


def validate_runtime_record(filename: str, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Pre-commit validation before appending record to runtime storage.
    Enforces primary key presence, uniqueness, foreign key validity, and schema constraints.
    """
    errors: List[str] = []
    id_col = ID_COLUMNS.get(filename)
    if id_col:
        pk = str(record.get(id_col) or "").strip()
        if not pk:
            errors.append(f"Missing required primary key '{id_col}' in {filename}")
        else:
            existing_records = get_all_records(filename)
            existing_pks = {str(r.get(id_col) or "").strip() for r in existing_records}
            if pk in existing_pks:
                errors.append(f"Duplicate primary key '{pk}' for table {filename}")

    # Foreign key references
    if filename == "case_persons.csv":
        cid = str(record.get("case_id") or "").strip()
        pid = str(record.get("person_id") or "").strip()
        if not cid:
            errors.append("case_persons record missing case_id")
        else:
            existing_cases = {str(r.get("case_id") or "").strip() for r in get_all_records("cases.csv")}
            if cid not in existing_cases:
                errors.append(f"case_persons references non-existent case_id: '{cid}'")
        if not pid:
            errors.append("case_persons record missing person_id")
        else:
            existing_persons = {str(r.get("person_id") or "").strip() for r in get_all_records("persons.csv")}
            if pid not in existing_persons:
                errors.append(f"case_persons references non-existent person_id: '{pid}'")

    elif filename == "cases.csv":
        status = str(record.get("status") or "").strip().upper()
        valid_statuses = {"OPEN", "CLOSED", "UNDER INVESTIGATION", "CHARGESHEETED"}
        if status and status not in valid_statuses:
            errors.append(f"Invalid case status '{status}'. Expected one of {valid_statuses}")
        fir = str(record.get("fir_number") or "").strip()
        if fir and check_fir_exists(fir):
            errors.append(f"Duplicate FIR number '{fir}' already exists")

    elif filename == "transactions.csv":
        amt = record.get("amount")
        if amt is not None and str(amt).strip():
            try:
                amt_val = float(str(amt).replace(",", "").strip())
                if amt_val <= 0:
                    errors.append(f"Transaction amount must be positive, got {amt_val}")
            except ValueError:
                errors.append(f"Invalid non-numeric transaction amount: '{amt}'")

    return (len(errors) == 0, errors)


def append_runtime_record(filename: str, record: Dict[str, Any], validate: bool = True) -> None:
    """
    Appends a single record dictionary to backend/data/runtime/<filename>.
    Thread-safe and creates header if file is new.
    Performs pre-commit schema and integrity validation unless validate=False.
    """
    if validate:
        is_valid, errors = validate_runtime_record(filename, record)
        if not is_valid:
            raise ValueError(f"Pre-commit runtime validation failed for {filename}: {'; '.join(errors)}")

    ensure_runtime_dir()
    filepath = os.path.join(RUNTIME_DIR, filename)
    fieldnames = SCHEMAS.get(filename)
    
    with _STORE_LOCK:
        file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
        
        # If fieldnames not explicitly registered, infer from record
        if not fieldnames:
            fieldnames = list(record.keys())
            
        with open(filepath, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            if not file_exists:
                writer.writeheader()
            writer.writerow(record)


def check_fir_exists(fir_number: str) -> bool:
    """
    Checks whether a FIR number already exists across baseline or runtime cases.
    Comparison is trimmed and case-insensitive.
    """
    if not fir_number or not fir_number.strip():
        return False
    target = fir_number.strip().lower()
    cases = get_all_records("cases.csv")
    for c in cases:
        existing = (c.get("fir_number") or "").strip().lower()
        if existing and existing == target:
            return True
    return False


def get_next_id(prefix: str, id_key: str, filename: str, digits: int = 3) -> str:
    """
    Dynamically scans baseline + runtime records and allocates highest existing ID + 1.
    Never hardcodes ID limits.
    """
    records = get_all_records(filename)
    max_num = 0
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)(?:-.*)?$")
    
    for r in records:
        val = (r.get(id_key) or "").strip()
        m = pattern.match(val)
        if m:
            try:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
                
    next_num = max_num + 1
    return f"{prefix}-{next_num:0{digits}d}"


def get_next_case_id() -> str:
    """Allocates next case ID: highest existing CASE-N + 1."""
    return get_next_id("CASE", "case_id", "cases.csv", digits=3)


def get_next_person_id() -> str:
    """Allocates next person ID: highest existing PERSON-N + 1."""
    return get_next_id("PERSON", "person_id", "persons.csv", digits=3)


def get_next_cp_id() -> str:
    """Allocates next case-person association ID: CPA-N + 1."""
    return get_next_id("CPA", "cp_id", "case_persons.csv", digits=4)


def get_next_phone_id() -> str:
    """Allocates next phone ID: PHONE-N + 1."""
    return get_next_id("PHONE", "phone_id", "phones.csv", digits=3)


def get_next_vehicle_id() -> str:
    """Allocates next vehicle ID: VEHICLE-N + 1."""
    return get_next_id("VEHICLE", "vehicle_id", "vehicles.csv", digits=3)


def get_next_bank_account_id() -> str:
    """Allocates next bank account ID: BANK-N + 1."""
    return get_next_id("BANK", "bank_account_id", "bank_accounts.csv", digits=3)


def clear_runtime_data() -> None:
    """
    Helper for testing and reset procedures.
    Safely deletes all files in backend/data/runtime/.
    Does NOT affect backend/data/*.csv baseline files.
    """
    if not os.path.exists(RUNTIME_DIR):
        return
    with _STORE_LOCK:
        for f in os.listdir(RUNTIME_DIR):
            fpath = os.path.join(RUNTIME_DIR, f)
            if os.path.isfile(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass
