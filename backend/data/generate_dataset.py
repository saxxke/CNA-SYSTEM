import os
import csv
import random
from datetime import datetime, timedelta

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

def get_random_date(start_year=2023, end_year=2026):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 6, 1)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return (start_date + timedelta(days=random_number_of_days)).strftime('%Y-%m-%d')

# Fictional reference data
FIRST_NAMES = ["Amit", "Rahul", "Priya", "Sneha", "Vikram", "Suresh", "Ramesh", "Deepa", "Anjali", "Neha", "Rohit", "Mohit", "Anand", "Ravi", "Sanjay", "Rakesh", "Meena", "Geeta", "Sunita", "Anita"]
LAST_NAMES = ["Sharma", "Verma", "Gupta", "Singh", "Kumar", "Das", "Bose", "Sen", "Patel", "Shah", "Reddy", "Nair", "Iyer", "Joshi", "Desai", "Mishra", "Pandey", "Tiwari", "Yadav", "Chauhan"]
CITIES = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Surat"]
STATES = ["Maharashtra", "Delhi", "Karnataka", "Telangana", "Tamil Nadu", "West Bengal", "Maharashtra", "Gujarat", "Rajasthan", "Gujarat"]

def create_dataset():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Generate Cases (50)
    cases = []
    case_types = ["financial fraud", "cyber fraud", "identity theft", "organized theft", "online scam", "vehicle-related fraud"]
    case_statuses = ["OPEN", "CLOSED", "UNDER INVESTIGATION"]
    for i in range(1, 51):
        cases.append({
            "case_id": f"CASE-{i:03d}",
            "case_title": f"Fictional Investigation {i:03d}",
            "case_type": random.choice(case_types),
            "date_opened": get_random_date(),
            "description": f"Synthetic case report regarding {random.choice(case_types)} detected in fictional scenario {i}.",
            "status": random.choice(case_statuses)
        })

    # Generate Phones (50)
    phones = []
    phone_variations = {} # map original to variations for ER testing
    for i in range(1, 51):
        base_num = f"9{random.randint(100000000, 999999999)}"
        # create variations for ER
        if i % 10 == 0:
            phones.append({"phone_id": f"PHONE-{i:03d}", "phone_number": f"+91 {base_num}", "phone_type": "MOBILE"})
            phones.append({"phone_id": f"PHONE-{i:03d}-V1", "phone_number": base_num, "phone_type": "MOBILE"})
            phones.append({"phone_id": f"PHONE-{i:03d}-V2", "phone_number": f"{base_num[:5]}-{base_num[5:]}", "phone_type": "MOBILE"})
        else:
            phones.append({"phone_id": f"PHONE-{i:03d}", "phone_number": base_num, "phone_type": "MOBILE"})
            
    # Generate Vehicles (30)
    vehicles = []
    for i in range(1, 31):
        base_reg = f"WB{random.randint(10, 99)}XX{random.randint(1000, 9999)}"
        if i % 10 == 0:
            vehicles.append({"vehicle_id": f"VEHICLE-{i:03d}", "registration_number": base_reg, "vehicle_type": "CAR", "model": "Hatchback"})
            vehicles.append({"vehicle_id": f"VEHICLE-{i:03d}-V1", "registration_number": f"WB-{base_reg[2:4]}-XX-{base_reg[6:]}", "vehicle_type": "CAR", "model": "Hatchback"})
        else:
            vehicles.append({"vehicle_id": f"VEHICLE-{i:03d}", "registration_number": base_reg, "vehicle_type": "SUV", "model": "Sedan"})

    # Generate Bank Accounts (40)
    bank_accounts = []
    bank_names = ["Fictional Bank A", "Fictional Bank B", "Fictional Bank C"]
    for i in range(1, 41):
        acc_num = f"{random.randint(1000000000, 9999999999)}"
        bank_accounts.append({"bank_account_id": f"BANK-{i:03d}", "account_number": acc_num, "bank_name": random.choice(bank_names), "account_type": "SAVINGS"})
        if i % 10 == 0:
            bank_accounts.append({"bank_account_id": f"BANK-{i:03d}-V1", "account_number": f"{acc_num[:4]} {acc_num[4:]}", "bank_name": random.choice(bank_names), "account_type": "SAVINGS"})

    # Generate Locations (30)
    locations = []
    for i in range(1, 31):
        city_idx = random.randint(0, len(CITIES)-1)
        locations.append({
            "location_id": f"LOCATION-{i:03d}",
            "location_name": f"Fictional Sector {random.randint(1, 100)}, {CITIES[city_idx]}",
            "location_type": random.choice(["RESIDENTIAL", "COMMERCIAL"]),
            "city": CITIES[city_idx],
            "state": STATES[city_idx]
        })

    # Generate Organizations (20)
    organizations = []
    for i in range(1, 21):
        organizations.append({
            "organization_id": f"ORG-{i:03d}",
            "organization_name": f"Fictional Enterprise {i}",
            "organization_type": random.choice(["CORPORATE", "NGO", "SHELL_COMPANY"]),
            "location_id": f"LOCATION-{random.randint(1, 30):03d}"
        })

    # Generate Persons (150)
    persons = []
    for i in range(1, 151):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        aliases = ""
        # 10% chance of alias/name variation ER testing
        if i % 10 == 0:
            aliases = f"{first} {last[0]}."
            name = f"{first} K. {last}"
            persons.append({"person_id": f"PERSON-{i:03d}-V1", "name": f"{first[0]}. {last}", "aliases": "", "phone_id": "", "bank_account_id": "", "vehicle_id": "", "location_id": "", "organization_id": ""})

        persons.append({
            "person_id": f"PERSON-{i:03d}",
            "name": name,
            "aliases": aliases,
            "phone_id": f"PHONE-{random.randint(1, 50):03d}",
            "bank_account_id": f"BANK-{random.randint(1, 40):03d}",
            "vehicle_id": f"VEHICLE-{random.randint(1, 30):03d}",
            "location_id": f"LOCATION-{random.randint(1, 30):03d}",
            "organization_id": f"ORG-{random.randint(1, 20):03d}" if random.random() > 0.5 else ""
        })
        
    # Generate Ground Truth & Communications/Transactions & Cross-Case
    communications = []
    transactions = []
    ground_truth = []
    
    # We will build 10 explicit cross-case networks
    cross_case_networks = [
        # Network 1 (Mandatory example)
        {"cases": ["CASE-001", "CASE-014"], "persons": ["PERSON-017", "PERSON-043"], "phone": "PHONE-004"},
        # Network 2
        {"cases": ["CASE-002", "CASE-025"], "persons": ["PERSON-022", "PERSON-055"], "phone": "PHONE-010"},
        # Network 3
        {"cases": ["CASE-005", "CASE-030"], "persons": ["PERSON-033", "PERSON-066"], "phone": "PHONE-015"},
        # Network 4
        {"cases": ["CASE-008", "CASE-040"], "persons": ["PERSON-011", "PERSON-099"], "phone": "PHONE-020"},
        # Network 5
        {"cases": ["CASE-012", "CASE-045"], "persons": ["PERSON-044", "PERSON-102"], "phone": "PHONE-025"},
        # Network 6
        {"cases": ["CASE-015", "CASE-048"], "persons": ["PERSON-052", "PERSON-115"], "phone": "PHONE-030"},
        # Network 7
        {"cases": ["CASE-018", "CASE-049"], "persons": ["PERSON-077", "PERSON-125"], "phone": "PHONE-035"},
        # Network 8
        {"cases": ["CASE-020", "CASE-050"], "persons": ["PERSON-088", "PERSON-140"], "phone": "PHONE-040"},
        # Network 9
        {"cases": ["CASE-003", "CASE-011"], "persons": ["PERSON-005", "PERSON-031"], "bank": "BANK-005"},
        # Network 10
        {"cases": ["CASE-007", "CASE-019"], "persons": ["PERSON-009", "PERSON-061"], "bank": "BANK-012"},
    ]
    
    comm_idx = 1
    txn_idx = 1
    gt_idx = 1
    
    for net in cross_case_networks:
        c1, c2 = net["cases"]
        p1, p2 = net["persons"]
        
        # Ground truth positive connections
        ground_truth.append({"ground_truth_id": f"GT-{gt_idx}", "source_entity_id": p1, "target_entity_id": c1, "relationship_type": "INVOLVED_IN", "case_id": c1, "expected_relationship": "1", "evidence_reference": "cases.csv"})
        gt_idx += 1
        ground_truth.append({"ground_truth_id": f"GT-{gt_idx}", "source_entity_id": p2, "target_entity_id": c2, "relationship_type": "INVOLVED_IN", "case_id": c2, "expected_relationship": "1", "evidence_reference": "cases.csv"})
        gt_idx += 1
        
        if "phone" in net:
            phone = net["phone"]
            # p1 involved in c1, p2 involved in c2
            communications.append({
                "communication_id": f"COMM-{comm_idx}",
                "case_id": c1,
                "source_person_id": p1,
                "target_person_id": p2,
                "phone_id": phone,
                "date": get_random_date(),
                "communication_type": "CALL",
                "description": f"{p1} contacted {p2} using {phone} regarding investigation material."
            })
            comm_idx += 1
            ground_truth.append({"ground_truth_id": f"GT-{gt_idx}", "source_entity_id": p1, "target_entity_id": p2, "relationship_type": "CONTACTED", "case_id": c1, "expected_relationship": "1", "evidence_reference": f"COMM-{comm_idx-1}"})
            gt_idx += 1
        elif "bank" in net:
            bank = net["bank"]
            transactions.append({
                "transaction_id": f"TXN-{txn_idx}",
                "case_id": c1,
                "source_person_id": p1,
                "target_person_id": p2,
                "source_account_id": f"BANK-{random.randint(1, 40):03d}",
                "target_account_id": bank,
                "amount": round(random.uniform(100, 50000), 2),
                "date": get_random_date(),
                "description": f"{p1} transferred funds to an account {bank} associated with {p2}."
            })
            txn_idx += 1
            ground_truth.append({"ground_truth_id": f"GT-{gt_idx}", "source_entity_id": p1, "target_entity_id": p2, "relationship_type": "TRANSFERRED_TO", "case_id": c1, "expected_relationship": "1", "evidence_reference": f"TXN-{txn_idx-1}"})
            gt_idx += 1
            
    # Add negative ground truth examples
    for i in range(10):
        p_rand1 = f"PERSON-{random.randint(1, 150):03d}"
        p_rand2 = f"PERSON-{random.randint(1, 150):03d}"
        if p_rand1 != p_rand2:
            ground_truth.append({"ground_truth_id": f"GT-{gt_idx}", "source_entity_id": p_rand1, "target_entity_id": p_rand2, "relationship_type": "CONTACTED", "case_id": "", "expected_relationship": "0", "evidence_reference": "N/A"})
            gt_idx += 1
            
    # Fill in some random noise data for comms and txns
    for _ in range(50):
        c_rand = f"CASE-{random.randint(1, 50):03d}"
        p_rand1 = f"PERSON-{random.randint(1, 150):03d}"
        p_rand2 = f"PERSON-{random.randint(1, 150):03d}"
        if p_rand1 != p_rand2:
            communications.append({
                "communication_id": f"COMM-{comm_idx}",
                "case_id": c_rand,
                "source_person_id": p_rand1,
                "target_person_id": p_rand2,
                "phone_id": f"PHONE-{random.randint(1, 50):03d}",
                "date": get_random_date(),
                "communication_type": "SMS",
                "description": f"Routine check: {p_rand1} texted {p_rand2}."
            })
            comm_idx += 1
            transactions.append({
                "transaction_id": f"TXN-{txn_idx}",
                "case_id": c_rand,
                "source_person_id": p_rand1,
                "target_person_id": p_rand2,
                "source_account_id": f"BANK-{random.randint(1, 40):03d}",
                "target_account_id": f"BANK-{random.randint(1, 40):03d}",
                "amount": round(random.uniform(500, 10000), 2),
                "date": get_random_date(),
                "description": f"Invoice payment from {p_rand1} to {p_rand2}."
            })
            txn_idx += 1

    # Write all CSVs
    def write_csv(filename, data):
        if not data: return
        with open(os.path.join(DATA_DIR, filename), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    write_csv("cases.csv", cases)
    write_csv("phones.csv", phones)
    write_csv("vehicles.csv", vehicles)
    write_csv("bank_accounts.csv", bank_accounts)
    write_csv("locations.csv", locations)
    write_csv("organizations.csv", organizations)
    write_csv("persons.csv", persons)
    write_csv("communications.csv", communications)
    write_csv("transactions.csv", transactions)
    write_csv("ground_truth.csv", ground_truth)

    print("Dataset generation complete!")

if __name__ == "__main__":
    create_dataset()
