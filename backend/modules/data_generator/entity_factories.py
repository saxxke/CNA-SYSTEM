"""
entity_factories.py
===================
Deterministic entity factories for synthetic records.
Allocates unique sequential primary keys and guarantees collision-free FIR numbers.
"""

import random
from typing import List, Dict, Any, Tuple
from modules.data_generator.config import (
    FIRST_NAMES_MALE, FIRST_NAMES_FEMALE, LAST_NAMES, OCCUPATIONS,
    LOCATIONS_DATA, OFFENCE_SPECS, BANK_NAMES, VEHICLE_TYPES,
    ORGANIZATION_TYPES
)

class IDTracker:
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.counter = 0

    def next_id(self) -> str:
        self.counter += 1
        return f"{self.prefix}-{self.counter:04d}"

class EntityFactories:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.person_id_gen = IDTracker("PERSON")
        self.case_id_gen = IDTracker("CASE")
        self.phone_id_gen = IDTracker("PHONE")
        self.bank_id_gen = IDTracker("BANK")
        self.vehicle_id_gen = IDTracker("VEHICLE")
        self.location_id_gen = IDTracker("LOCATION")
        self.org_id_gen = IDTracker("ORG")
        self.alias_id_gen = IDTracker("ALIAS")
        self.fam_id_gen = IDTracker("FAM")
        self.cp_id_gen = IDTracker("CP")
        self.comm_id_gen = IDTracker("COMM")
        self.txn_id_gen = IDTracker("TXN")
        self.gt_id_gen = IDTracker("GT")
        
        self.fir_counter = 0

    def generate_unique_fir(self, year: int) -> str:
        self.fir_counter += 1
        return f"FIR-{year}-{self.fir_counter:04d}"

    def create_locations(self, count: int) -> List[Dict[str, Any]]:
        locations = []
        for _ in range(count):
            loc_ref = self.rng.choice(LOCATIONS_DATA)
            loc_id = self.location_id_gen.next_id()
            locations.append({
                "location_id": loc_id,
                "city": loc_ref["city"],
                "district": loc_ref["district"],
                "state": loc_ref["state"],
                "pincode": loc_ref["pincode"],
                "police_station": loc_ref["police_station"]
            })
        return locations

    def create_phones(self, count: int) -> List[Dict[str, Any]]:
        phones = []
        seen_numbers = set()
        providers = ["Jio", "Airtel", "Vodafone-Idea", "BSNL"]
        phone_types = ["SmartPhone", "FeaturePhone", "VirtualNumber"]
        
        for idx in range(1, count + 1):
            phone_id = self.phone_id_gen.next_id()
            # Monotonic deterministic unique phone number
            num_suffix = f"{idx:05d}"
            phone_num = f"+91 98765 {num_suffix}"
            imei = f"86{idx:013d}"
            phones.append({
                "phone_id": phone_id,
                "phone_number": phone_num,
                "phone_type": self.rng.choice(phone_types),
                "imei": imei,
                "service_provider": self.rng.choice(providers)
            })
        return phones

    def create_bank_accounts(self, count: int) -> List[Dict[str, Any]]:
        accounts = []
        for idx in range(1, count + 1):
            acc_id = self.bank_id_gen.next_id()
            bname = self.rng.choice(BANK_NAMES)
            acc_num = f"{1000000000 + idx}"
            ifsc = f"SBIN00{self.rng.randint(1000, 9999)}"
            accounts.append({
                "bank_account_id": acc_id,
                "account_number": acc_num,
                "bank_name": bname,
                "ifsc_code": ifsc,
                "branch": f"{bname} Main Branch"
            })
        return accounts

    def create_vehicles(self, count: int) -> List[Dict[str, Any]]:
        vehicles = []
        colors = ["White", "Silver", "Black", "Grey", "Blue", "Red"]
        for idx in range(1, count + 1):
            veh_id = self.vehicle_id_gen.next_id()
            reg_no = f"WB-01-AB-{idx:04d}"
            vehicles.append({
                "vehicle_id": veh_id,
                "registration_number": reg_no,
                "vehicle_type": self.rng.choice(VEHICLE_TYPES),
                "model": "Standard Synthetic Model",
                "color": self.rng.choice(colors)
            })
        return vehicles

    def create_organizations(self, count: int) -> List[Dict[str, Any]]:
        orgs = []
        for idx in range(1, count + 1):
            org_id = self.org_id_gen.next_id()
            name_base = self.rng.choice(LAST_NAMES)
            org_type = self.rng.choice(ORGANIZATION_TYPES)
            orgs.append({
                "organization_id": org_id,
                "organization_name": f"{name_base} {org_type}",
                "organization_type": org_type,
                "registration_number": f"REG-ORG-{idx:04d}"
            })
        return orgs

    def create_persons(self, count: int, phones: List[Dict[str, Any]], bank_accounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        persons = []
        for idx in range(1, count + 1):
            pid = self.person_id_gen.next_id()
            is_male = self.rng.random() < 0.70
            first_name = self.rng.choice(FIRST_NAMES_MALE if is_male else FIRST_NAMES_FEMALE)
            last_name = self.rng.choice(LAST_NAMES)
            full_name = f"{first_name} {last_name}"
            
            loc = self.rng.choice(LOCATIONS_DATA)
            age = self.rng.randint(22, 65)
            birth_year = 2024 - age
            dob = f"{birth_year}-{self.rng.randint(1, 12):02d}-{self.rng.randint(1, 28):02d}"
            
            # Asset assignment (reusing pool deterministically)
            assigned_phone = phones[(idx - 1) % len(phones)]["phone_id"] if phones else ""
            assigned_bank = bank_accounts[(idx - 1) % len(bank_accounts)]["bank_account_id"] if bank_accounts else ""
            
            persons.append({
                "person_id": pid,
                "full_name": full_name,
                "gender": "Male" if is_male else "Female",
                "date_of_birth": dob,
                "age": age,
                "occupation": self.rng.choice(OCCUPATIONS),
                "city": loc["city"],
                "district": loc["district"],
                "phone_id": assigned_phone,
                "bank_account_id": assigned_bank
            })
        return persons

    def create_cases(self, count: int) -> List[Dict[str, Any]]:
        cases = []
        for _ in range(count):
            cid = self.case_id_gen.next_id()
            offence = self.rng.choice(OFFENCE_SPECS)
            loc = self.rng.choice(LOCATIONS_DATA)
            year = self.rng.randint(2021, 2024)
            fir = self.generate_unique_fir(year)
            status = "OPEN" if self.rng.random() < 0.65 else "CLOSED"
            title = offence["title_template"].format(loc=loc["city"])
            
            cases.append({
                "case_id": cid,
                "fir_number": fir,
                "offence_category": offence["offence_category"],
                "title": title,
                "legal_section": offence["legal_section"],
                "year": year,
                "location": loc["city"],
                "district": loc["district"],
                "police_station": loc["police_station"],
                "status": status
            })
        return cases
