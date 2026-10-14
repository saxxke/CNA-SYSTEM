"""
generate_rich_dataset.py
========================
Generates a rich, realistic SYNTHETIC/DEMONSTRATION dataset for the
Criminal Network Intelligence System.

ALL persons, addresses, phone numbers, case records, and family
information are ENTIRELY FICTIONAL. No real personal data is used.
Do not use this dataset to make claims about any real individual.

Produces:
  persons.csv        – ~200 persons with full demographic profiles
  aliases.csv        – alias/variant name records
  families.csv       – family relationship table (FATHER/MOTHER/SPOUSE/CHILD/BROTHER/SISTER)
  phones.csv         – ~80 phones (some deliberately shared between persons)
  bank_accounts.csv  – ~60 accounts
  vehicles.csv       – ~50 vehicles (some deliberately shared)
  locations.csv      – ~40 locations with district metadata
  organizations.csv  – ~25 organizations
  cases.csv          – ~250 cases with rich offence metadata
  case_persons.csv   – explicit many-to-many case-person associations
  communications.csv – ~100 human-readable communication records
  transactions.csv   – ~80 human-readable financial transaction records
  ground_truth.csv   – validated positive and negative relationship examples
"""

import os
import csv
import random
from datetime import datetime, timedelta, date

random.seed(42)   # Deterministic output for regression safety

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ──────────────────────────────────────────────────────────────────────────────
# REFERENCE POOLS
# ──────────────────────────────────────────────────────────────────────────────

MALE_FIRST_NAMES = [
    "Arjun", "Vikram", "Rahul", "Amit", "Rajesh", "Suresh", "Ajay", "Deepak",
    "Manoj", "Ravi", "Anil", "Sanjay", "Ashok", "Nitin", "Pradeep", "Vivek",
    "Ganesh", "Ramesh", "Mukesh", "Satish", "Arvind", "Vinod", "Bharat",
    "Dinesh", "Harish", "Jitendra", "Kamal", "Lalit", "Mohan", "Naresh",
    "Omkar", "Prakash", "Rakesh", "Sachin", "Tarun", "Umesh", "Varun",
    "Yogesh", "Sudhir", "Prashant", "Devraj", "Akshay", "Lokesh", "Hemant",
    "Girish", "Firoz", "Chandrakant", "Balram", "Anand", "Kiran",
]

FEMALE_FIRST_NAMES = [
    "Priya", "Sunita", "Rekha", "Anita", "Kavita", "Meena", "Geeta", "Sita",
    "Lata", "Usha", "Vandana", "Puja", "Nisha", "Shobha", "Asha", "Seema",
    "Radha", "Mamta", "Savita", "Tanuja", "Hema", "Jyoti", "Kamla", "Lalita",
    "Mala", "Nalini", "Padma", "Pratibha", "Sudha", "Tara", "Uma",
    "Vinita", "Vimla", "Farida", "Divya", "Arti", "Bharati", "Chandra",
    "Renu", "Sarita",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Das", "Bose", "Sen",
    "Patel", "Shah", "Reddy", "Nair", "Iyer", "Joshi", "Desai", "Mishra",
    "Pandey", "Tiwari", "Yadav", "Chauhan", "Malhotra", "Arora", "Khanna",
    "Mehta", "Chaudhary", "Dubey", "Sinha", "Rao", "Pillai", "Naidu",
    "Chatterjee", "Banerjee", "Mukherjee", "Roy", "Ghosh", "Agarwal",
    "Jain", "Saxena", "Kapoor", "Srivastava", "Lal", "Prasad",
]

OCCUPATIONS = [
    "Driver", "Shopkeeper", "Farmer", "Mechanic", "Contractor", "Trader",
    "Student", "Labourer", "Hawker", "Security Guard", "Clerk",
    "Business Owner", "Real Estate Agent", "Courier", "Hotel Staff",
    "Auto-Rickshaw Driver", "Electrician", "Plumber", "Daily Wage Worker",
    "Unemployed", "Tailor", "Grocery Merchant",
]

EDUCATION_LEVELS = [
    "Illiterate", "Primary School", "Middle School", "High School",
    "Intermediate (12th)", "Graduate", "Post Graduate",
]

GENDERS = ["Male", "Female"]

OFFENCE_CATEGORIES = [
    "Theft", "Robbery", "Kidnapping", "Fraud", "Attempted Murder", "Murder",
    "Molestation", "Assault", "Burglary", "Extortion", "Property Offence",
    "Cybercrime", "Forgery", "Criminal Intimidation",
]

CASE_STATUSES = ["OPEN", "CLOSED", "UNDER INVESTIGATION", "CHARGESHEETED"]

VEHICLE_TYPES = ["CAR", "MOTORCYCLE", "AUTO-RICKSHAW", "TRUCK", "VAN"]
VEHICLE_MODELS = [
    "Alto", "Swift", "Bolero", "Scorpio", "Innova", "Splendor", "Pulsar",
    "Activa", "Avenger", "Eeco", "Omni", "Tata Sumo", "Maruti 800",
]

ORG_TYPES = ["CORPORATE", "SHELL_COMPANY", "PROPRIETORSHIP", "PARTNERSHIP", "NGO"]

# Cities with their districts and police station naming convention
CITY_DATA = [
    {"city": "Kolkata",    "district": "Kolkata",            "state": "West Bengal"},
    {"city": "Kolkata",    "district": "North 24 Parganas",  "state": "West Bengal"},
    {"city": "Howrah",     "district": "Howrah",             "state": "West Bengal"},
    {"city": "Mumbai",     "district": "Mumbai City",        "state": "Maharashtra"},
    {"city": "Mumbai",     "district": "Mumbai Suburban",    "state": "Maharashtra"},
    {"city": "Thane",      "district": "Thane",              "state": "Maharashtra"},
    {"city": "Pune",       "district": "Pune",               "state": "Maharashtra"},
    {"city": "Delhi",      "district": "Central Delhi",      "state": "Delhi"},
    {"city": "Delhi",      "district": "North Delhi",        "state": "Delhi"},
    {"city": "Delhi",      "district": "South Delhi",        "state": "Delhi"},
    {"city": "Delhi",      "district": "East Delhi",         "state": "Delhi"},
    {"city": "Bengaluru",  "district": "Bengaluru Urban",    "state": "Karnataka"},
    {"city": "Bengaluru",  "district": "Bengaluru Rural",    "state": "Karnataka"},
    {"city": "Chennai",    "district": "Chennai",            "state": "Tamil Nadu"},
    {"city": "Hyderabad",  "district": "Hyderabad",          "state": "Telangana"},
    {"city": "Hyderabad",  "district": "Rangareddy",         "state": "Telangana"},
    {"city": "Ahmedabad",  "district": "Ahmedabad",          "state": "Gujarat"},
    {"city": "Surat",      "district": "Surat",              "state": "Gujarat"},
    {"city": "Jaipur",     "district": "Jaipur",             "state": "Rajasthan"},
    {"city": "Patna",      "district": "Patna",              "state": "Bihar"},
    {"city": "Lucknow",    "district": "Lucknow",            "state": "Uttar Pradesh"},
    {"city": "Kanpur",     "district": "Kanpur Nagar",       "state": "Uttar Pradesh"},
    {"city": "Bhopal",     "district": "Bhopal",             "state": "Madhya Pradesh"},
    {"city": "Raipur",     "district": "Raipur",             "state": "Chhattisgarh"},
    {"city": "Nagpur",     "district": "Nagpur",             "state": "Maharashtra"},
]

LOCALITY_NAMES = [
    "Shastri Nagar", "Gandhi Colony", "Nehru Road", "Patel Chowk", "Station Road",
    "Market Area", "Old City Quarter", "New Colony", "Transport Nagar", "Industrial Area",
    "Civil Lines", "Lake View", "Green Park", "Sector 7", "Sector 12", "Sector 21",
    "Sector 35", "MG Road", "Ring Road Mohalla", "Bypass Colony",
]


def rand_date(start_year=2022, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).strftime("%Y-%m-%d")


def rand_dob(min_age=18, max_age=65):
    today = date.today()
    age = random.randint(min_age, max_age)
    birth_year = today.year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    return date(birth_year, birth_month, birth_day).strftime("%Y-%m-%d")


def gen_phone():
    """Generate a fictional 10-digit Indian mobile number starting with 7, 8, or 9."""
    prefix = random.choice([7, 8, 9])
    rest = random.randint(100000000, 999999999)
    return f"{prefix}{rest}"


def gen_account():
    """Generate a fictional 10-digit bank account number."""
    return str(random.randint(1000000000, 9999999999))


def gen_vehicle_reg(state_code="WB"):
    """Generate a synthetic vehicle registration number."""
    num = random.randint(10, 99)
    letters = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=2))
    serial = random.randint(1000, 9999)
    return f"{state_code}{num:02d}{letters}{serial}"


STATE_CODES = {
    "West Bengal": "WB", "Maharashtra": "MH", "Delhi": "DL",
    "Karnataka": "KA", "Tamil Nadu": "TN", "Telangana": "TS",
    "Gujarat": "GJ", "Rajasthan": "RJ", "Bihar": "BR",
    "Uttar Pradesh": "UP", "Madhya Pradesh": "MP", "Chhattisgarh": "CG",
}

# ──────────────────────────────────────────────────────────────────────────────
# INVESTIGATION SCENARIOS (deliberate, evidence-backed)
# ──────────────────────────────────────────────────────────────────────────────
# Each scenario defines person IDs (0-indexed into the scenario persons list),
# shared resources, and narrative context.
# These become CASE-001 through CASE-040 approximately.

SCENARIOS = [
    # ─── SCENARIO 1: The Raipur Ransom Network (Kidnapping + Extortion) ───
    {
        "id": "S1",
        "name": "Raipur Ransom Network",
        "persons": [
            {"idx": 0, "first": "Arjun",   "last": "Mehta",    "gender": "Male",   "city_key": 23},
            {"idx": 1, "first": "Vikram",   "last": "Singh",    "gender": "Male",   "city_key": 23},
            {"idx": 2, "first": "Renu",     "last": "Sharma",   "gender": "Female", "city_key": 23},
            {"idx": 3, "first": "Mohan",    "last": "Yadav",    "gender": "Male",   "city_key": 23},
            # Family member - NOT in any case
            {"idx": 4, "first": "Suresh",   "last": "Mehta",    "gender": "Male",   "city_key": 23},
        ],
        "families": [
            {"p1": 0, "p2": 4, "rel": "FATHER"},   # Suresh is Arjun's father
            {"p1": 1, "p2": 2, "rel": "SPOUSE"},    # Vikram married Renu
        ],
        "phone_shared": True,   # persons 0 and 1 share a phone
        "vehicle_shared": True, # persons 1 and 3 share a vehicle
        "cases": [
            {"offence": "Kidnapping",            "persons": [0, 1, 3], "city_key": 23},
            {"offence": "Extortion",             "persons": [0, 1],    "city_key": 23},
            {"offence": "Criminal Intimidation", "persons": [2, 3],    "city_key": 23},
        ],
        "comms": [
            {"from": 0, "to": 1, "re": "ransom demand"},
            {"from": 1, "to": 3, "re": "vehicle handover instructions"},
            {"from": 2, "to": 0, "re": "target location information"},
        ],
        "txns": [
            {"from": 1, "to": 0, "amt": 85000, "re": "payment for services"},
            {"from": 3, "to": 1, "amt": 42000, "re": "operational expenses"},
        ],
    },

    # ─── SCENARIO 2: Online Fraud Ring (Cybercrime + Forgery + Fraud) ───
    {
        "id": "S2",
        "name": "Kolkata Cyber Fraud Ring",
        "persons": [
            {"idx": 5,  "first": "Deepak",  "last": "Arora",    "gender": "Male",   "city_key": 0},
            {"idx": 6,  "first": "Sunita",  "last": "Bhat",     "gender": "Female", "city_key": 0},
            {"idx": 7,  "first": "Rajesh",  "last": "Malhotra", "gender": "Male",   "city_key": 0},
            {"idx": 8,  "first": "Kavita",  "last": "Desai",    "gender": "Female", "city_key": 1},
            # Bridge to S1 - Renu Sharma (idx=2) appears in S2 case 0
            # Family member
            {"idx": 9,  "first": "Anand",   "last": "Arora",    "gender": "Male",   "city_key": 0},
        ],
        "families": [
            {"p1": 5, "p2": 9,  "rel": "BROTHER"},
            {"p1": 6, "p2": 7,  "rel": "SPOUSE"},
        ],
        "bank_shared": True,   # Persons 5, 6, 7 share a bank account (ORG account)
        "org_shared": True,
        "cases": [
            {"offence": "Cybercrime", "persons": [5, 6, 7],    "city_key": 0, "bridge_s1": 2},
            {"offence": "Forgery",    "persons": [5, 8],        "city_key": 0},
            {"offence": "Fraud",      "persons": [6, 7, 8],     "city_key": 1},
        ],
        "comms": [
            {"from": 5, "to": 6, "re": "phishing scheme coordination"},
            {"from": 7, "to": 5, "re": "document forgery instructions"},
            {"from": 8, "to": 6, "re": "money mule transaction"},
        ],
        "txns": [
            {"from": 5, "to": 7, "amt": 125000, "re": "proceeds of fraud"},
            {"from": 6, "to": 8, "amt": 63000,  "re": "commission payment"},
        ],
    },

    # ─── SCENARIO 3: Vehicle Theft Gang (Theft + Robbery + Burglary) ───
    {
        "id": "S3",
        "name": "Mumbai-Pune Vehicle Theft Gang",
        "persons": [
            {"idx": 10, "first": "Sanjay",  "last": "Dubey",    "gender": "Male",   "city_key": 3},
            {"idx": 11, "first": "Ajay",    "last": "Tiwari",   "gender": "Male",   "city_key": 6},
            {"idx": 12, "first": "Ram",     "last": "Das",      "gender": "Male",   "city_key": 3},
            {"idx": 13, "first": "Priya",   "last": "Dubey",    "gender": "Female", "city_key": 3},
            {"idx": 14, "first": "Naresh",  "last": "Yadav",    "gender": "Male",   "city_key": 6},
        ],
        "families": [
            {"p1": 10, "p2": 13, "rel": "SPOUSE"},
            {"p1": 11, "p2": 14, "rel": "BROTHER"},
        ],
        "vehicle_shared": True,   # Persons 10, 11, 12 share a vehicle
        "cases": [
            {"offence": "Theft",    "persons": [10, 11, 12], "city_key": 3},
            {"offence": "Robbery",  "persons": [10, 12],     "city_key": 3},
            {"offence": "Burglary", "persons": [11, 14],     "city_key": 6},
            {"offence": "Theft",    "persons": [10, 11],     "city_key": 6},
        ],
        "comms": [
            {"from": 10, "to": 11, "re": "vehicle handover location"},
            {"from": 12, "to": 10, "re": "buyer contact details"},
            {"from": 14, "to": 11, "re": "warehouse coordinates"},
        ],
        "txns": [
            {"from": 11, "to": 10, "amt": 55000, "re": "stolen vehicle proceeds"},
            {"from": 12, "to": 10, "amt": 30000, "re": "sale of stolen goods"},
        ],
    },

    # ─── SCENARIO 4: High-Priority Multi-Case Individual ───
    {
        "id": "S4",
        "name": "Multi-Case Individual Scenario",
        "persons": [
            {"idx": 15, "first": "Balram",  "last": "Sinha",    "gender": "Male",   "city_key": 7},
            {"idx": 16, "first": "Geeta",   "last": "Sinha",    "gender": "Female", "city_key": 7},
            {"idx": 17, "first": "Sudhir",  "last": "Kapoor",   "gender": "Male",   "city_key": 8},
        ],
        "families": [
            {"p1": 15, "p2": 16, "rel": "SPOUSE"},
        ],
        "cases": [
            {"offence": "Assault",               "persons": [15],       "city_key": 7},
            {"offence": "Robbery",               "persons": [15, 17],   "city_key": 7},
            {"offence": "Criminal Intimidation", "persons": [15],       "city_key": 8},
            {"offence": "Extortion",             "persons": [15, 17],   "city_key": 8},
            {"offence": "Theft",                 "persons": [15],       "city_key": 9},
            {"offence": "Fraud",                 "persons": [15, 17],   "city_key": 7},
            {"offence": "Forgery",               "persons": [15],       "city_key": 8},
        ],
        "comms": [
            {"from": 15, "to": 17, "re": "extortion target details"},
            {"from": 17, "to": 15, "re": "payment collection instructions"},
        ],
        "txns": [
            {"from": 17, "to": 15, "amt": 90000, "re": "extortion proceeds"},
        ],
    },

    # ─── SCENARIO 5: Property Crime & Murder (Kolkata) ───
    {
        "id": "S5",
        "name": "Kolkata Property Crime Network",
        "persons": [
            {"idx": 18, "first": "Prakash", "last": "Roy",      "gender": "Male",   "city_key": 0},
            {"idx": 19, "first": "Mamta",   "last": "Ghosh",    "gender": "Female", "city_key": 0},
            {"idx": 20, "first": "Dinesh",  "last": "Chatterjee","gender": "Male",  "city_key": 1},
            {"idx": 21, "first": "Hema",    "last": "Roy",      "gender": "Female", "city_key": 0},
        ],
        "families": [
            {"p1": 18, "p2": 21, "rel": "SISTER"},
        ],
        "cases": [
            {"offence": "Property Offence", "persons": [18, 20],  "city_key": 0},
            {"offence": "Murder",           "persons": [18, 19],  "city_key": 0},
            {"offence": "Assault",          "persons": [19, 20],  "city_key": 1},
        ],
        "comms": [
            {"from": 18, "to": 19, "re": "property encroachment plan"},
            {"from": 20, "to": 18, "re": "legal documents forgery"},
        ],
        "txns": [
            {"from": 18, "to": 20, "amt": 200000, "re": "illegal property transfer"},
        ],
    },

    # ─── SCENARIO 6: Cross-City Financial Fraud (Mumbai+Delhi+Bengaluru) ───
    {
        "id": "S6",
        "name": "Cross-City Financial Fraud",
        "persons": [
            {"idx": 22, "first": "Vivek",   "last": "Jain",     "gender": "Male",   "city_key": 3},
            {"idx": 23, "first": "Nisha",   "last": "Kapoor",   "gender": "Female", "city_key": 7},
            {"idx": 24, "first": "Omkar",   "last": "Naidu",    "gender": "Male",   "city_key": 11},
            {"idx": 25, "first": "Farida",  "last": "Khan",     "gender": "Female", "city_key": 3},
            {"idx": 26, "first": "Tarun",   "last": "Jain",     "gender": "Male",   "city_key": 3},
        ],
        "families": [
            {"p1": 22, "p2": 26, "rel": "BROTHER"},
            {"p1": 22, "p2": 25, "rel": "SPOUSE"},
        ],
        "bank_shared": True,
        "cases": [
            {"offence": "Fraud",      "persons": [22, 23, 24], "city_key": 3},
            {"offence": "Fraud",      "persons": [22, 25],     "city_key": 7},
            {"offence": "Cybercrime", "persons": [24, 26],     "city_key": 11},
        ],
        "comms": [
            {"from": 22, "to": 23, "re": "fraudulent investment scheme details"},
            {"from": 24, "to": 22, "re": "online account access credentials"},
            {"from": 25, "to": 22, "re": "money transfer confirmation"},
        ],
        "txns": [
            {"from": 23, "to": 22, "amt": 450000, "re": "fraudulent fund transfer"},
            {"from": 22, "to": 24, "amt": 180000, "re": "commission for cyber access"},
            {"from": 25, "to": 22, "amt": 95000,  "re": "hawala transfer"},
        ],
    },

    # ─── SCENARIO 7: Molestation & Assault Cases (Jaipur) ───
    {
        "id": "S7",
        "name": "Jaipur Assault Cases",
        "persons": [
            {"idx": 27, "first": "Yogesh",  "last": "Chauhan",  "gender": "Male",   "city_key": 18},
            {"idx": 28, "first": "Lalit",   "last": "Saxena",   "gender": "Male",   "city_key": 18},
            {"idx": 29, "first": "Seema",   "last": "Chauhan",  "gender": "Female", "city_key": 18},
        ],
        "families": [
            {"p1": 27, "p2": 29, "rel": "SISTER"},
        ],
        "cases": [
            {"offence": "Molestation", "persons": [27, 28], "city_key": 18},
            {"offence": "Assault",     "persons": [28],     "city_key": 18},
        ],
        "comms": [
            {"from": 27, "to": 28, "re": "witness intimidation"},
        ],
        "txns": [],
    },

    # ─── SCENARIO 8: Bridge Person (Connects S1 and S3) ───
    {
        "id": "S8",
        "name": "Bridge Person Scenario",
        "persons": [
            {"idx": 30, "first": "Hemant",  "last": "Pandey",   "gender": "Male",   "city_key": 19},
        ],
        "families": [],
        "cases": [
            # Bridge person is in both S1 case type and S3 case type
            {"offence": "Kidnapping", "persons": [30, 0],   "city_key": 23},  # Links to Arjun Mehta
            {"offence": "Theft",      "persons": [30, 10],  "city_key": 3},   # Links to Sanjay Dubey
        ],
        "comms": [
            {"from": 30, "to": 0,  "re": "coordination with ransom network"},
            {"from": 30, "to": 10, "re": "stolen vehicle buyer information"},
        ],
        "txns": [
            {"from": 30, "to": 0, "amt": 35000, "re": "ransom coordination fee"},
        ],
    },
]

# Total scenario persons: indices 0-30 (31 persons)

# ──────────────────────────────────────────────────────────────────────────────
# MAIN GENERATOR
# ──────────────────────────────────────────────────────────────────────────────

def create_dataset():
    os.makedirs(DATA_DIR, exist_ok=True)

    # ── 1. LOCATIONS ──────────────────────────────────────────────────────────
    locations = []
    for i, city_d in enumerate(CITY_DATA):
        locality = random.choice(LOCALITY_NAMES)
        pin = f"{random.randint(100, 999)}{random.randint(100, 999)}"
        locations.append({
            "location_id":   f"LOCATION-{i+1:03d}",
            "locality":      f"Fictional {locality}",
            "location_name": f"Fictional {locality}, {city_d['city']}",
            "location_type": random.choice(["RESIDENTIAL", "COMMERCIAL"]),
            "city":          city_d["city"],
            "district":      city_d["district"],
            "state":         city_d["state"],
            "pin_code":      pin,
        })
    # Add 15 more filler locations
    for i in range(len(CITY_DATA), 40):
        city_d = random.choice(CITY_DATA)
        locality = random.choice(LOCALITY_NAMES)
        pin = f"{random.randint(100, 999)}{random.randint(100, 999)}"
        locations.append({
            "location_id":   f"LOCATION-{i+1:03d}",
            "locality":      f"Fictional {locality}",
            "location_name": f"Fictional {locality}, {city_d['city']}",
            "location_type": random.choice(["RESIDENTIAL", "COMMERCIAL"]),
            "city":          city_d["city"],
            "district":      city_d["district"],
            "state":         city_d["state"],
            "pin_code":      pin,
        })
    loc_ids = [l["location_id"] for l in locations]

    # ── 2. ORGANIZATIONS ──────────────────────────────────────────────────────
    organizations = []
    org_names_pool = [
        "Sunrise Traders", "Apex Enterprises", "Royal Commerce Co.",
        "National Logistics Pvt. Ltd.", "Sterling Solutions",
        "Diamond Constructions", "Global Exports Ltd.",
        "Pioneer Real Estate", "Suncity Properties", "Metro Supply Chain",
        "United Finance Group", "Horizon Tech Services", "Lakshmi Trading Co.",
        "Bharat Courier Services", "New India Ventures",
        "Eastern Commercial House", "Western Goods Distributors",
        "Central Garments Pvt. Ltd.", "Rural Agri Traders", "City Auto Parts",
        "Reliable Security Services", "Prime Hospitality", "Dev Constructions",
        "Prestige Associates", "Green Valley Enterprises",
    ]
    for i, name in enumerate(org_names_pool[:25]):
        organizations.append({
            "organization_id":   f"ORG-{i+1:03d}",
            "organization_name": f"Fictional {name}",
            "organization_type": random.choice(ORG_TYPES),
            "location_id":       random.choice(loc_ids),
        })
    org_ids = [o["organization_id"] for o in organizations]

    # ── 3. PHONES ─────────────────────────────────────────────────────────────
    phones = []
    phone_map = {}  # phone_id -> phone record
    for i in range(1, 81):
        base_num = gen_phone()
        # Variations for entity resolution testing (every 10th)
        if i % 10 == 0:
            phones.append({"phone_id": f"PHONE-{i:03d}",    "phone_number": f"+91 {base_num}", "phone_type": "MOBILE"})
            phones.append({"phone_id": f"PHONE-{i:03d}-V1", "phone_number": base_num,          "phone_type": "MOBILE"})
            phones.append({"phone_id": f"PHONE-{i:03d}-V2", "phone_number": f"{base_num[:5]}-{base_num[5:]}", "phone_type": "MOBILE"})
        else:
            phones.append({"phone_id": f"PHONE-{i:03d}", "phone_number": base_num, "phone_type": "MOBILE"})
        phone_map[f"PHONE-{i:03d}"] = base_num
    phone_ids = [p["phone_id"] for p in phones if "-V" not in p["phone_id"]]

    # ── 4. BANK ACCOUNTS ──────────────────────────────────────────────────────
    bank_names = [
        "Fictional State Bank of India", "Fictional Punjab National Bank",
        "Fictional Bank of Baroda", "Fictional HDFC Bank", "Fictional ICICI Bank",
    ]
    bank_accounts = []
    for i in range(1, 61):
        acc_num = gen_account()
        bank_accounts.append({
            "bank_account_id": f"BANK-{i:03d}",
            "account_number":  acc_num,
            "bank_name":       random.choice(bank_names),
            "account_type":    random.choice(["SAVINGS", "CURRENT"]),
        })
        if i % 10 == 0:
            bank_accounts.append({
                "bank_account_id": f"BANK-{i:03d}-V1",
                "account_number":  f"{acc_num[:4]} {acc_num[4:]}",
                "bank_name":       random.choice(bank_names),
                "account_type":    "SAVINGS",
            })
    bank_ids = [b["bank_account_id"] for b in bank_accounts if "-V" not in b["bank_account_id"]]

    # ── 5. VEHICLES ───────────────────────────────────────────────────────────
    vehicles = []
    for i in range(1, 51):
        city_d = random.choice(CITY_DATA)
        sc = STATE_CODES.get(city_d["state"], "XX")
        reg = gen_vehicle_reg(sc)
        vtype = random.choice(VEHICLE_TYPES)
        model = random.choice(VEHICLE_MODELS)
        vehicles.append({
            "vehicle_id":          f"VEHICLE-{i:03d}",
            "registration_number": reg,
            "vehicle_type":        vtype,
            "model":               model,
            "color":               random.choice(["White", "Black", "Silver", "Red", "Blue", "Grey"]),
        })
        if i % 10 == 0:
            # Variant for entity resolution
            vehicles.append({
                "vehicle_id":          f"VEHICLE-{i:03d}-V1",
                "registration_number": f"{sc}-{reg[2:4]}-{reg[4:6]}-{reg[6:]}",
                "vehicle_type":        vtype,
                "model":               model,
                "color":               random.choice(["White", "Black", "Silver"]),
            })
    vehicle_ids = [v["vehicle_id"] for v in vehicles if "-V" not in v["vehicle_id"]]

    # ── 6. BUILD SCENARIO PERSONS & BACKGROUND PERSONS ───────────────────────
    # Collect all scenario person definitions
    scenario_person_defs = {}
    for sc in SCENARIOS:
        for p in sc["persons"]:
            idx = p["idx"]
            if idx not in scenario_person_defs:
                scenario_person_defs[idx] = p
                scenario_person_defs[idx]["scenario_id"] = sc["id"]

    # Assign IDs and resources to scenario persons
    scenario_persons = {}  # idx -> full person record
    SHARED_PHONE = {}    # scenario_id -> phone_id (shared phones for scenarios)
    SHARED_VEHICLE = {}  # scenario_id -> vehicle_id
    SHARED_BANK = {}     # scenario_id -> bank_id

    # Pre-allocate some phones/vehicles/banks for deliberate sharing
    for sc in SCENARIOS:
        sc_id = sc["id"]
        if sc.get("phone_shared"):
            SHARED_PHONE[sc_id] = phone_ids[int(sc_id[1:]) - 1]  # deterministic
        if sc.get("vehicle_shared"):
            SHARED_VEHICLE[sc_id] = vehicle_ids[int(sc_id[1:]) - 1]
        if sc.get("bank_shared"):
            SHARED_BANK[sc_id] = bank_ids[int(sc_id[1:]) - 1]

    all_person_records = []
    person_idx_to_id = {}  # scenario person index -> PERSON-XXX id

    # Generate scenario persons first (PERSON-001 to PERSON-031)
    for idx in sorted(scenario_person_defs.keys()):
        pdef = scenario_person_defs[idx]
        pid = f"PERSON-{idx+1:03d}"
        person_idx_to_id[idx] = pid

        city_d = CITY_DATA[pdef["city_key"]]
        gender = pdef["gender"]
        dob = rand_dob(25, 55)
        birth_year = int(dob[:4])
        age = date.today().year - birth_year
        loc_id = f"LOCATION-{pdef['city_key']+1:03d}"
        full_name = f"{pdef['first']} {pdef['last']}"

        # Assign scenario-appropriate phone
        sc_id = pdef["scenario_id"]
        if sc_id in SHARED_PHONE and idx in [p["idx"] for p in next(s for s in SCENARIOS if s["id"] == sc_id)["persons"]][:2]:
            phone_id = SHARED_PHONE[sc_id]
        else:
            phone_id = random.choice(phone_ids)

        phone_id_2 = random.choice(phone_ids) if random.random() < 0.4 else ""

        if sc_id in SHARED_VEHICLE and idx in [p["idx"] for p in next(s for s in SCENARIOS if s["id"] == sc_id)["persons"]][:3]:
            vehicle_id = SHARED_VEHICLE[sc_id]
        else:
            vehicle_id = random.choice(vehicle_ids) if random.random() < 0.8 else ""

        vehicle_id_2 = random.choice(vehicle_ids) if random.random() < 0.2 else ""

        if sc_id in SHARED_BANK and idx in [p["idx"] for p in next(s for s in SCENARIOS if s["id"] == sc_id)["persons"]][:3]:
            bank_id = SHARED_BANK[sc_id]
        else:
            bank_id = random.choice(bank_ids)

        bank_id_2 = random.choice(bank_ids) if random.random() < 0.3 else ""

        org_id = random.choice(org_ids) if random.random() < 0.6 else ""

        rec = {
            "person_id":        pid,
            "full_name":        full_name,
            "first_name":       pdef["first"],
            "last_name":        pdef["last"],
            "gender":           gender,
            "date_of_birth":    dob,
            "age":              age,
            "occupation":       random.choice(OCCUPATIONS),
            "education":        random.choice(EDUCATION_LEVELS),
            "address":          f"Fictional H.No. {random.randint(1, 999)}, {random.choice(LOCALITY_NAMES)}",
            "locality":         f"Fictional {random.choice(LOCALITY_NAMES)}",
            "city":             city_d["city"],
            "district":         city_d["district"],
            "state":            city_d["state"],
            "pin_code":         f"{random.randint(100, 999)}{random.randint(100, 999)}",
            "phone_id":         phone_id,
            "phone_id_2":       phone_id_2,
            "bank_account_id":  bank_id,
            "bank_account_id_2":bank_id_2,
            "vehicle_id":       vehicle_id,
            "vehicle_id_2":     vehicle_id_2,
            "location_id":      loc_id,
            "organization_id":  org_id,
            "email":            f"fictional.{pdef['first'].lower()}.{pdef['last'].lower()}@synthetic-demo.invalid",
        }
        all_person_records.append(rec)
        scenario_persons[idx] = rec

    # Generate background persons (PERSON-032 to PERSON-200)
    used_names = {(r["first_name"], r["last_name"]) for r in all_person_records}
    for i in range(len(scenario_person_defs), 200):
        pid = f"PERSON-{i+1:03d}"
        gender = random.choice(GENDERS)
        first = random.choice(MALE_FIRST_NAMES if gender == "Male" else FEMALE_FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        # Ensure unique names for realism
        attempts = 0
        while (first, last) in used_names and attempts < 20:
            first = random.choice(MALE_FIRST_NAMES if gender == "Male" else FEMALE_FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            attempts += 1
        used_names.add((first, last))

        city_d = random.choice(CITY_DATA)
        dob = rand_dob(18, 70)
        birth_year = int(dob[:4])
        age = date.today().year - birth_year
        loc_id = random.choice(loc_ids)

        phone_id = random.choice(phone_ids)
        phone_id_2 = random.choice(phone_ids) if random.random() < 0.35 else ""
        bank_id = random.choice(bank_ids)
        bank_id_2 = random.choice(bank_ids) if random.random() < 0.25 else ""
        vehicle_id = random.choice(vehicle_ids) if random.random() < 0.7 else ""
        vehicle_id_2 = random.choice(vehicle_ids) if random.random() < 0.15 else ""
        org_id = random.choice(org_ids) if random.random() < 0.55 else ""

        rec = {
            "person_id":        pid,
            "full_name":        f"{first} {last}",
            "first_name":       first,
            "last_name":        last,
            "gender":           gender,
            "date_of_birth":    dob,
            "age":              age,
            "occupation":       random.choice(OCCUPATIONS),
            "education":        random.choice(EDUCATION_LEVELS),
            "address":          f"Fictional H.No. {random.randint(1, 999)}, {random.choice(LOCALITY_NAMES)}",
            "locality":         f"Fictional {random.choice(LOCALITY_NAMES)}",
            "city":             city_d["city"],
            "district":         city_d["district"],
            "state":            city_d["state"],
            "pin_code":         f"{random.randint(100, 999)}{random.randint(100, 999)}",
            "phone_id":         phone_id,
            "phone_id_2":       phone_id_2,
            "bank_account_id":  bank_id,
            "bank_account_id_2":bank_id_2,
            "vehicle_id":       vehicle_id,
            "vehicle_id_2":     vehicle_id_2,
            "location_id":      loc_id,
            "organization_id":  org_id,
            "email":            f"fictional.{first.lower()}.{last.lower()}{i}@synthetic-demo.invalid",
        }
        all_person_records.append(rec)

    # ── 7. ALIASES ────────────────────────────────────────────────────────────
    aliases = []
    alias_idx = 1
    # Scenario persons with known aliases
    scenario_alias_map = {
        0: [("Arjun M.", "Common short form"), ("A. Mehta", "Official record variant")],
        5: [("D. Arora", "Record variant")],
        10: [("S. Dubey", "Common usage")],
        15: [("Ballu", "Street alias"), ("B. Sinha", "Record variant")],
        22: [("V. Jain", "Record variant")],
    }
    for person_idx, alias_list in scenario_alias_map.items():
        pid = f"PERSON-{person_idx+1:03d}"
        for alias_name, alias_type in alias_list:
            aliases.append({
                "alias_id":   f"ALIAS-{alias_idx:03d}",
                "person_id":  pid,
                "alias_name": alias_name,
                "alias_type": alias_type,
            })
            alias_idx += 1

    # Generate ER-test alias variants for every 10th background person
    for i in range(31, 200, 10):
        if i < len(all_person_records):
            p = all_person_records[i]
            pid = p["person_id"]
            aliases.append({
                "alias_id":   f"ALIAS-{alias_idx:03d}",
                "person_id":  pid,
                "alias_name": f"{p['first_name'][0]}. {p['last_name']}",
                "alias_type": "Record variant",
            })
            alias_idx += 1

    # ── 8. FAMILIES ───────────────────────────────────────────────────────────
    REL_INVERSE = {
        "FATHER": "CHILD",  "MOTHER": "CHILD",
        "CHILD": "FATHER",  # simplified — could be either
        "SPOUSE": "SPOUSE",
        "BROTHER": "BROTHER", "SISTER": "SISTER",
    }
    families = []
    fam_idx = 1

    for sc in SCENARIOS:
        sc_persons = {p["idx"]: p for p in sc["persons"]}
        for fam in sc.get("families", []):
            p1_idx, p2_idx = fam["p1"], fam["p2"]
            rel = fam["rel"]
            p1_id = person_idx_to_id.get(p1_idx, f"PERSON-{p1_idx+1:03d}")
            p2_id = person_idx_to_id.get(p2_idx, f"PERSON-{p2_idx+1:03d}")
            families.append({
                "family_id":            f"FAM-{fam_idx:03d}",
                "person_id":            p1_id,
                "related_person_id":    p2_id,
                "relationship_subtype": rel,
                "notes":                "Synthetic family record. Family relationship does not imply case involvement.",
            })
            fam_idx += 1
            # Inverse relationship
            inv = REL_INVERSE.get(rel, "RELATED_TO")
            families.append({
                "family_id":            f"FAM-{fam_idx:03d}",
                "person_id":            p2_id,
                "related_person_id":    p1_id,
                "relationship_subtype": inv,
                "notes":                "Synthetic family record. Family relationship does not imply case involvement.",
            })
            fam_idx += 1

    # Add random family relationships between background persons
    background_person_ids = [p["person_id"] for p in all_person_records[31:]]
    family_rels_types = ["FATHER", "MOTHER", "SPOUSE", "BROTHER", "SISTER"]
    for _ in range(50):
        p1_id = random.choice(background_person_ids)
        p2_id = random.choice(background_person_ids)
        if p1_id != p2_id:
            rel = random.choice(family_rels_types)
            families.append({
                "family_id":            f"FAM-{fam_idx:03d}",
                "person_id":            p1_id,
                "related_person_id":    p2_id,
                "relationship_subtype": rel,
                "notes":                "Synthetic family record. Family relationship does not imply case involvement.",
            })
            fam_idx += 1

    # ── 9. CASES ──────────────────────────────────────────────────────────────
    cases = []
    case_persons_list = []  # For case_persons.csv
    case_idx = 1
    cp_idx = 1
    scenario_case_ids = {}  # (scenario_id, case_number) -> CASE-XXX

    # Scenario cases first
    for sc in SCENARIOS:
        for ci, case_def in enumerate(sc.get("cases", [])):
            city_d = CITY_DATA[case_def["city_key"]]
            ps_num = random.randint(1, 12)
            case_id = f"CASE-{case_idx:03d}"
            scenario_case_ids[(sc["id"], ci)] = case_id

            # Offence category → legal section mapping (synthetic)
            offence = case_def["offence"]
            legal_section = {
                "Theft": "IPC 379", "Robbery": "IPC 392", "Kidnapping": "IPC 363",
                "Fraud": "IPC 420", "Attempted Murder": "IPC 307", "Murder": "IPC 302",
                "Molestation": "IPC 354", "Assault": "IPC 323", "Burglary": "IPC 457",
                "Extortion": "IPC 384", "Property Offence": "IPC 425",
                "Cybercrime": "IT Act 66C", "Forgery": "IPC 465",
                "Criminal Intimidation": "IPC 506",
            }.get(offence, "IPC 420")

            fir = f"FIR-SYNTH-{city_d['district'][:3].upper()}-{case_idx:04d}"
            cases.append({
                "case_id":          case_id,
                "case_title":       f"Synthetic Case Record {case_idx:03d} — {offence} — {city_d['district']}",
                "offence_category": offence,
                "legal_section":    legal_section,
                "fir_number":       fir,
                "date_opened":      rand_date(2022, 2025),
                "description":      (
                    f"Synthetic case record regarding {offence.lower()} associated with registered "
                    f"case record in fictional scenario {case_idx}. District: {city_d['district']}, "
                    f"State: {city_d['state']}. This record is for demonstration purposes only."
                ),
                "status":           random.choice(CASE_STATUSES),
                "police_station":   f"Fictional PS No.{ps_num}, {city_d['city']}",
                "district":         city_d["district"],
                "state":            city_d["state"],
                "location_id":      f"LOCATION-{case_def['city_key']+1:03d}",
            })

            # Case-person associations
            for p_idx in case_def["persons"]:
                p_id = person_idx_to_id.get(p_idx, f"PERSON-{p_idx+1:03d}")
                case_persons_list.append({
                    "cp_id":       f"CPA-{cp_idx:04d}",
                    "case_id":     case_id,
                    "person_id":   p_id,
                    "association": "Associated with registered case record. Requires human verification.",
                    "role":        "SUBJECT",
                    "source":      "STRUCTURED_METADATA",
                })
                cp_idx += 1

            # Bridge case for S8
            if sc["id"] == "S8" and "bridge_s1" not in case_def:
                pass  # already handled by person_idx reference

            case_idx += 1

    # Background cases (CASE-{next} to CASE-250)
    background_person_ids_all = [p["person_id"] for p in all_person_records]
    while case_idx <= 250:
        city_d = random.choice(CITY_DATA)
        offence = random.choice(OFFENCE_CATEGORIES)
        legal_section = {
            "Theft": "IPC 379", "Robbery": "IPC 392", "Kidnapping": "IPC 363",
            "Fraud": "IPC 420", "Attempted Murder": "IPC 307", "Murder": "IPC 302",
            "Molestation": "IPC 354", "Assault": "IPC 323", "Burglary": "IPC 457",
            "Extortion": "IPC 384", "Property Offence": "IPC 425",
            "Cybercrime": "IT Act 66C", "Forgery": "IPC 465",
            "Criminal Intimidation": "IPC 506",
        }.get(offence, "IPC 420")
        ps_num = random.randint(1, 20)
        loc_id = random.choice(loc_ids)
        case_id = f"CASE-{case_idx:03d}"
        fir = f"FIR-SYNTH-{city_d['district'][:3].upper()}-{case_idx:04d}"

        cases.append({
            "case_id":          case_id,
            "case_title":       f"Synthetic Case Record {case_idx:03d} — {offence} — {city_d['district']}",
            "offence_category": offence,
            "legal_section":    legal_section,
            "fir_number":       fir,
            "date_opened":      rand_date(2021, 2025),
            "description":      (
                f"Synthetic case record regarding {offence.lower()} in fictional scenario {case_idx}. "
                f"District: {city_d['district']}, State: {city_d['state']}. "
                "For demonstration purposes only."
            ),
            "status":           random.choice(CASE_STATUSES),
            "police_station":   f"Fictional PS No.{ps_num}, {city_d['city']}",
            "district":         city_d["district"],
            "state":            city_d["state"],
            "location_id":      loc_id,
        })

        # 65% of background cases have 1–3 associated persons; 35% are isolated
        if random.random() < 0.65:
            num_persons = random.randint(1, 3)
            selected = random.sample(background_person_ids_all, min(num_persons, len(background_person_ids_all)))
            for p_id in selected:
                case_persons_list.append({
                    "cp_id":       f"CPA-{cp_idx:04d}",
                    "case_id":     case_id,
                    "person_id":   p_id,
                    "association": "Associated with registered case record. Requires human verification.",
                    "role":        "SUBJECT",
                    "source":      "STRUCTURED_METADATA",
                })
                cp_idx += 1

        case_idx += 1

    case_ids = [c["case_id"] for c in cases]
    all_person_ids = [p["person_id"] for p in all_person_records]

    # ── 10. COMMUNICATIONS ────────────────────────────────────────────────────
    communications = []
    comm_idx = 1

    # Scenario communications (human-readable with names)
    for sc in SCENARIOS:
        for ci, comm_def in enumerate(sc.get("comms", [])):
            from_idx = comm_def["from"]
            to_idx   = comm_def["to"]
            subject  = comm_def["re"]

            p_from_rec = scenario_persons.get(from_idx)
            p_to_rec   = scenario_persons.get(to_idx)
            if not p_from_rec or not p_to_rec:
                continue

            from_name   = p_from_rec["full_name"]
            to_name     = p_to_rec["full_name"]
            from_id     = p_from_rec["person_id"]
            to_id       = p_to_rec["person_id"]
            phone_num   = phone_map.get(p_from_rec["phone_id"], "unknown")

            # Find an associated case for this communication
            sc_cases_for_from = [
                scenario_case_ids.get((sc["id"], ci2))
                for ci2, c2 in enumerate(sc.get("cases", []))
                if from_idx in c2["persons"] or to_idx in c2["persons"]
            ]
            case_id_ref = sc_cases_for_from[0] if sc_cases_for_from else random.choice(case_ids)

            comm_date = rand_date(2022, 2025)
            comm_type = random.choice(["CALL", "SMS", "WHATSAPP"])

            # Human-readable description — enables spaCy NER on names
            description = (
                f"On {comm_date}, {from_name} contacted {to_name} "
                f"using registered mobile number {phone_num} "
                f"regarding {subject}. Communication type: {comm_type}."
            )

            communications.append({
                "communication_id": f"COMM-{comm_idx:03d}",
                "case_id":          case_id_ref,
                "source_person_id": from_id,
                "target_person_id": to_id,
                "phone_id":         p_from_rec["phone_id"],
                "date":             comm_date,
                "communication_type": comm_type,
                "description":      description,
            })
            comm_idx += 1

    # Background communications (also human-readable)
    all_persons_with_names = [(p["person_id"], p["full_name"], p["phone_id"]) for p in all_person_records]
    comm_subjects = [
        "financial transaction details", "property dispute discussion",
        "meeting location confirmation", "payment arrangement",
        "document delivery instructions", "vehicle handover plan",
        "travel arrangement", "business negotiation",
        "contact for further coordination", "routine check-in",
    ]
    for _ in range(80):
        p1_id, p1_name, p1_phone = random.choice(all_persons_with_names)
        p2_id, p2_name, p2_phone = random.choice(all_persons_with_names)
        if p1_id == p2_id:
            continue
        c_id = random.choice(case_ids)
        comm_date = rand_date(2021, 2025)
        subject = random.choice(comm_subjects)
        phone_num = phone_map.get(p1_phone, "unknown")
        comm_type = random.choice(["CALL", "SMS"])

        description = (
            f"On {comm_date}, {p1_name} contacted {p2_name} "
            f"using mobile number {phone_num} regarding {subject}."
        )

        communications.append({
            "communication_id": f"COMM-{comm_idx:03d}",
            "case_id":          c_id,
            "source_person_id": p1_id,
            "target_person_id": p2_id,
            "phone_id":         p1_phone,
            "date":             comm_date,
            "communication_type": comm_type,
            "description":      description,
        })
        comm_idx += 1

    # ── 11. TRANSACTIONS ──────────────────────────────────────────────────────
    transactions = []
    txn_idx = 1

    for sc in SCENARIOS:
        for ti, txn_def in enumerate(sc.get("txns", [])):
            from_idx = txn_def["from"]
            to_idx   = txn_def["to"]
            amt      = txn_def["amt"]
            reason   = txn_def["re"]

            p_from_rec = scenario_persons.get(from_idx)
            p_to_rec   = scenario_persons.get(to_idx)
            if not p_from_rec or not p_to_rec:
                continue

            from_name = p_from_rec["full_name"]
            to_name   = p_to_rec["full_name"]
            from_id   = p_from_rec["person_id"]
            to_id     = p_to_rec["person_id"]
            src_bank  = p_from_rec["bank_account_id"]
            tgt_bank  = p_to_rec["bank_account_id"]

            sc_cases_for = [
                scenario_case_ids.get((sc["id"], ci2))
                for ci2, c2 in enumerate(sc.get("cases", []))
                if from_idx in c2["persons"] or to_idx in c2["persons"]
            ]
            case_id_ref = sc_cases_for[0] if sc_cases_for else random.choice(case_ids)
            txn_date = rand_date(2022, 2025)

            description = (
                f"On {txn_date}, {from_name} transferred ₹{amt:,} "
                f"to a bank account associated with {to_name} "
                f"regarding {reason}."
            )

            transactions.append({
                "transaction_id":    f"TXN-{txn_idx:03d}",
                "case_id":           case_id_ref,
                "source_person_id":  from_id,
                "target_person_id":  to_id,
                "source_account_id": src_bank,
                "target_account_id": tgt_bank,
                "amount":            amt,
                "date":              txn_date,
                "description":       description,
            })
            txn_idx += 1

    # Background transactions (human-readable)
    txn_subjects = [
        "payment for goods received", "loan repayment",
        "business transaction", "property advance",
        "service fee payment", "rental deposit",
    ]
    for _ in range(60):
        p1 = random.choice(all_person_records)
        p2 = random.choice(all_person_records)
        if p1["person_id"] == p2["person_id"]:
            continue
        amt = round(random.uniform(500, 500000), 2)
        c_id = random.choice(case_ids)
        txn_date = rand_date(2021, 2025)
        reason = random.choice(txn_subjects)

        description = (
            f"On {txn_date}, {p1['full_name']} transferred ₹{amt:,.2f} "
            f"to an account associated with {p2['full_name']} "
            f"regarding {reason}."
        )

        transactions.append({
            "transaction_id":    f"TXN-{txn_idx:03d}",
            "case_id":           c_id,
            "source_person_id":  p1["person_id"],
            "target_person_id":  p2["person_id"],
            "source_account_id": p1["bank_account_id"],
            "target_account_id": p2["bank_account_id"],
            "amount":            amt,
            "date":              txn_date,
            "description":       description,
        })
        txn_idx += 1

    # ── 12. GROUND TRUTH ──────────────────────────────────────────────────────
    ground_truth = []
    gt_idx = 1

    # Positive ground truth from scenario case-person associations
    for cp in case_persons_list:
        if cp["source"] == "STRUCTURED_METADATA":
            p_id = cp["person_id"]
            c_id = cp["case_id"]
            ground_truth.append({
                "ground_truth_id":     f"GT-{gt_idx:03d}",
                "source_entity_id":    p_id,
                "target_entity_id":    c_id,
                "relationship_type":   "INVOLVED_IN",
                "case_id":             c_id,
                "expected_relationship": "1",
                "evidence_reference":  "case_persons.csv",
            })
            gt_idx += 1
            if gt_idx > 80:  # cap positive GT to keep file manageable
                break

    # Positive ground truth from scenario communications
    for comm in communications[:30]:
        ground_truth.append({
            "ground_truth_id":     f"GT-{gt_idx:03d}",
            "source_entity_id":    comm["source_person_id"],
            "target_entity_id":    comm["target_person_id"],
            "relationship_type":   "CONTACTED",
            "case_id":             comm["case_id"],
            "expected_relationship": "1",
            "evidence_reference":  comm["communication_id"],
        })
        gt_idx += 1

    # Positive ground truth from scenario transactions
    for txn in transactions[:20]:
        ground_truth.append({
            "ground_truth_id":     f"GT-{gt_idx:03d}",
            "source_entity_id":    txn["source_person_id"],
            "target_entity_id":    txn["target_person_id"],
            "relationship_type":   "TRANSFERRED_TO",
            "case_id":             txn["case_id"],
            "expected_relationship": "1",
            "evidence_reference":  txn["transaction_id"],
        })
        gt_idx += 1

    # Negative ground truth (pairs with no known relationship)
    for _ in range(15):
        p1 = random.choice(all_person_ids)
        p2 = random.choice(all_person_ids)
        if p1 != p2:
            ground_truth.append({
                "ground_truth_id":     f"GT-{gt_idx:03d}",
                "source_entity_id":    p1,
                "target_entity_id":    p2,
                "relationship_type":   "CONTACTED",
                "case_id":             "",
                "expected_relationship": "0",
                "evidence_reference":  "N/A",
            })
            gt_idx += 1

    # ── 13. WRITE ALL CSVs ────────────────────────────────────────────────────
    def write_csv(filename, data):
        if not data:
            print(f"  [WARN] No data for {filename}, skipping.")
            return
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        print(f"  [OK]   {filename}: {len(data)} records")

    print("Generating rich synthetic dataset...")
    write_csv("locations.csv",      locations)
    write_csv("organizations.csv",  organizations)
    write_csv("phones.csv",         phones)
    write_csv("bank_accounts.csv",  bank_accounts)
    write_csv("vehicles.csv",       vehicles)
    write_csv("persons.csv",        all_person_records)
    write_csv("aliases.csv",        aliases)
    write_csv("families.csv",       families)
    write_csv("cases.csv",          cases)
    write_csv("case_persons.csv",   case_persons_list)
    write_csv("communications.csv", communications)
    write_csv("transactions.csv",   transactions)
    write_csv("ground_truth.csv",   ground_truth)

    print(f"\nDataset Summary:")
    print(f"  Locations:      {len(locations)}")
    print(f"  Organizations:  {len(organizations)}")
    print(f"  Phones:         {len(phones)}")
    print(f"  Bank Accounts:  {len(bank_accounts)}")
    print(f"  Vehicles:       {len(vehicles)}")
    print(f"  Persons:        {len(all_person_records)}")
    print(f"  Aliases:        {len(aliases)}")
    print(f"  Families:       {len(families)}")
    print(f"  Cases:          {len(cases)}")
    print(f"  Case-Persons:   {len(case_persons_list)}")
    print(f"  Communications: {len(communications)}")
    print(f"  Transactions:   {len(transactions)}")
    print(f"  Ground Truth:   {len(ground_truth)}")
    print("\nAll SYNTHETIC DEMONSTRATION DATA — no real personal information.")


if __name__ == "__main__":
    create_dataset()
