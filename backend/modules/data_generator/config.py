"""
config.py
=========
Configuration, profiles, reference tables, and schemas for the Step 22 Synthetic Investigation Data Generator.
"""

from typing import Dict, Any

PROFILES: Dict[str, Dict[str, int]] = {
    "SMALL": {
        "persons": 1000,
        "cases": 1250,
        "case_persons": 1800,
        "phones": 500,
        "bank_accounts": 450,
        "vehicles": 350,
        "locations": 250,
        "organizations": 150,
        "aliases": 200,
        "families": 350,
        "communications": 600,
        "transactions": 450,
        "ground_truth": 1000,
    },
    "MEDIUM": {
        "persons": 5000,
        "cases": 6000,
        "case_persons": 9200,
        "phones": 2600,
        "bank_accounts": 2400,
        "vehicles": 1800,
        "locations": 1200,
        "organizations": 800,
        "aliases": 1100,
        "families": 1800,
        "communications": 3100,
        "transactions": 2400,
        "ground_truth": 5500,
    },
    "LARGE": {
        "persons": 10000,
        "cases": 12000,
        "case_persons": 18500,
        "phones": 5200,
        "bank_accounts": 5000,
        "vehicles": 3600,
        "locations": 2500,
        "organizations": 1600,
        "aliases": 2200,
        "families": 3600,
        "communications": 6500,
        "transactions": 5000,
        "ground_truth": 12000,
    }
}

FIRST_NAMES_MALE = [
    "Arjun", "Vikram", "Rajesh", "Amit", "Rahul", "Suresh", "Ramesh", "Deepak",
    "Manoj", "Sanjay", "Anil", "Sunil", "Rakesh", "Vijay", "Ajay", "Dinesh",
    "Gaurav", "Pankaj", "Pradeep", "Alok", "Ashok", "Kunal", "Sumit", "Naveen",
    "Sachin", "Rohit", "Manish", "Abhishek", "Vivek", "Santosh", "Pawan", "Mukesh",
    "Dharmendra", "Jitendra", "Harish", "Subhash", "Nitin", "Satish", "Devendra", "Hemant"
]

FIRST_NAMES_FEMALE = [
    "Pooja", "Sunita", "Anita", "Geeta", "Rekha", "Sangeeta", "Meena", "Shobha",
    "Kavita", "Mamta", "Manju", "Poonam", "Ritu", "Seema", "Neetu", "Kiran",
    "Usha", "Shashi", "Sarita", "Asha", "Pushpa", "Champa", "Lata", "Vandana",
    "Babita", "Sushma", "Kamla", "Reena", "Jyoti", "Archana", "Radha", "Kusum"
]

LAST_NAMES = [
    "Mehta", "Singh", "Sharma", "Verma", "Gupta", "Kumar", "Yadav", "Patel",
    "Das", "Pandey", "Mishra", "Tiwari", "Shukla", "Banerjee", "Chatterjee", "Mukherjee",
    "Bose", "Ghosh", "Roy", "Dutta", "Sarkar", "Sen", "Chakraborty", "Bhattacharya",
    "Kaur", "Ali", "Khan", "Ahmed", "Ansari", "Hussain", "Siddiqui", "Qureshi",
    "Jain", "Agarwal", "Bansal", "Goyal", "Mittal", "Singhal", "Garg", "Joshi"
]

OCCUPATIONS = [
    "Clerk", "Accountant", "Driver", "Contractor", "Electrician", "Shopkeeper",
    "Mechanic", "Broker", "Security Guard", "Trader", "Technician", "Supervisor",
    "Sales Representative", "Delivery Agent", "Warehouse Assistant", "Plumber",
    "Carpenter", "Tailor", "Mason", "Transporter", "Real Estate Agent", "Consultant"
]

LOCATIONS_DATA = [
    {"city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "pincode": "700001", "police_station": "Park Street"},
    {"city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "pincode": "700019", "police_station": "Ballygunge"},
    {"city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "pincode": "700007", "police_station": "Burrabazar"},
    {"city": "Howrah", "district": "Howrah", "state": "West Bengal", "pincode": "711101", "police_station": "Howrah Town"},
    {"city": "Siliguri", "district": "Darjeeling", "state": "West Bengal", "pincode": "734001", "police_station": "Siliguri PS"},
    {"city": "Raipur", "district": "Raipur", "state": "Chhattisgarh", "pincode": "492001", "police_station": "Civil Lines"},
    {"city": "Bilaspur", "district": "Bilaspur", "state": "Chhattisgarh", "pincode": "495001", "police_station": "City Kotwali"},
    {"city": "Durg", "district": "Durg", "state": "Chhattisgarh", "pincode": "491001", "police_station": "Durg Sadar"},
    {"city": "Mumbai", "district": "Mumbai City", "state": "Maharashtra", "pincode": "400001", "police_station": "Colaba"},
    {"city": "Mumbai", "district": "Mumbai Suburban", "state": "Maharashtra", "pincode": "400050", "police_station": "Bandra"},
    {"city": "Pune", "district": "Pune", "state": "Maharashtra", "pincode": "411001", "police_station": "Shivajinagar"},
    {"city": "Nagpur", "district": "Nagpur", "state": "Maharashtra", "pincode": "440001", "police_station": "Sitabuldi"},
    {"city": "Delhi", "district": "Central Delhi", "state": "Delhi", "pincode": "110001", "police_station": "Connaught Place"},
    {"city": "Delhi", "district": "South Delhi", "state": "Delhi", "pincode": "110017", "police_station": "Hauz Khas"},
    {"city": "Delhi", "district": "East Delhi", "state": "Delhi", "pincode": "110092", "police_station": "Preet Vihar"},
    {"city": "Ahmedabad", "district": "Ahmedabad", "state": "Gujarat", "pincode": "380001", "police_station": "Ellis Bridge"},
    {"city": "Surat", "district": "Surat", "state": "Gujarat", "pincode": "395001", "police_station": "Varachha"},
    {"city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "pincode": "600001", "police_station": "Flower Bazaar"},
    {"city": "Lucknow", "district": "Lucknow", "state": "Uttar Pradesh", "pincode": "226001", "police_station": "Hazratganj"},
    {"city": "Varanasi", "district": "Varanasi", "state": "Uttar Pradesh", "pincode": "221001", "police_station": "Dashashwamedh"}
]

OFFENCE_SPECS = [
    {"offence_category": "Kidnapping", "legal_section": "IPC 363/364A", "title_template": "Kidnapping and Extortion Case at {loc}"},
    {"offence_category": "Extortion", "legal_section": "IPC 384/386", "title_template": "Threat and Extortion Racket in {loc}"},
    {"offence_category": "Cybercrime", "legal_section": "IT Act 66D / IPC 420", "title_template": "Digital Identity Theft and Financial Scam at {loc}"},
    {"offence_category": "Forgery", "legal_section": "IPC 467/468/471", "title_template": "Forged Documentation and Property Fraud in {loc}"},
    {"offence_category": "Fraud", "legal_section": "IPC 420/406", "title_template": "Commercial Fraud and Embezzlement Syndicate at {loc}"},
    {"offence_category": "Theft", "legal_section": "IPC 379", "title_template": "Serial Asset and Vehicle Theft in {loc}"},
    {"offence_category": "Robbery", "legal_section": "IPC 392/397", "title_template": "Armed Robbery Incident at {loc}"},
    {"offence_category": "Burglary", "legal_section": "IPC 457/380", "title_template": "Nocturnal Commercial Burglary in {loc}"},
    {"offence_category": "Assault", "legal_section": "IPC 323/325", "title_template": "Physical Assault and Grievous Hurt Case at {loc}"},
    {"offence_category": "Murder", "legal_section": "IPC 302/120B", "title_template": "Targeted Homicide Investigation in {loc}"},
    {"offence_category": "Criminal Intimidation", "legal_section": "IPC 506", "title_template": "Intimidation and Witness Tampering at {loc}"}
]

COMMUNICATION_TYPES = ["PHONE_CALL", "WHATSAPP", "SMS", "ENCRYPTED_CALL"]
BANK_NAMES = ["State Bank of India", "HDFC Bank", "ICICI Bank", "Punjab National Bank", "Bank of Baroda", "Axis Bank", "Canara Bank"]
VEHICLE_TYPES = ["Sedan", "Hatchback", "SUV", "Motorcycle", "Van", "Truck"]
ORGANIZATION_TYPES = ["Trading Enterprise", "Logistics Agency", "Security Services", "Consultancy Group", "Export House", "Property Ventures"]
ROLES_IN_CASE = ["SUSPECT", "ASSOCIATE", "ACCUSED", "PERSON_OF_INTEREST", "WITNESS", "REPORTING_PERSON"]
FAMILY_RELATIONSHIPS = [
    ("FATHER", "SON"),
    ("MOTHER", "SON"),
    ("FATHER", "DAUGHTER"),
    ("MOTHER", "DAUGHTER"),
    ("BROTHER", "BROTHER"),
    ("SISTER", "BROTHER"),
    ("SISTER", "SISTER"),
    ("SPOUSE", "SPOUSE")
]
