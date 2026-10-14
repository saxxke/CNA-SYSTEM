# PS 26189 — Project Rules

## PROJECT

Project:
Smart India Hackathon 2026

Problem Statement:
PS 26189 — AI-Powered Criminal Network Analysis System

Project Type:
Internal Hackathon MVP

Development Mode:
Solo Developer + AI Coding Agent

---

# 1. PROJECT OBJECTIVE

Build a functional MVP demonstrating an AI-assisted investigation
intelligence platform.

The MVP should demonstrate:

Investigation Data
        ↓
NLP Preprocessing
        ↓
Entity Extraction
        ↓
Entity Normalization
        ↓
Embedding-Based Entity Resolution
        ↓
Relationship Extraction
        ↓
Relationship Confidence
        ↓
Knowledge Graph
        ↓
Graph Analytics
        ↓
Cross-Case Analysis
        ↓
Investigation Priority
        ↓
React Investigator Dashboard
        ↓
Grounded AI Investigation Assistant

The objective is to demonstrate the core concept clearly.

This is NOT a production law-enforcement system.

---

# 2. MVP FEATURES

The MVP must demonstrate:

1. Synthetic investigation data
2. NLP preprocessing
3. Named Entity Recognition
4. Structured entity extraction
5. Entity normalization
6. Embedding-assisted entity resolution
7. Relationship extraction
8. Relationship confidence estimation
9. Knowledge graph construction
10. Cross-case relationship discovery
11. Graph analytics
12. Potential connector detection
13. Explainable investigation priority
14. Interactive network visualization
15. Investigation timeline
16. React investigator dashboard
17. Grounded AI investigation assistant
18. Demonstration scenarios

---

# 3. TECHNOLOGY STACK

## FRONTEND

React
Vite
Tailwind CSS
React Router
Axios
Cytoscape.js
Recharts
Lucide React

## BACKEND

Python
FastAPI
Pandas
NetworkX
Pydantic
scikit-learn
spaCy
sentence-transformers
python-dotenv

## AI / ML

spaCy:
Named Entity Recognition

Regex / Rules:
Structured entity extraction

Sentence Transformers:
Entity similarity / entity resolution

scikit-learn Logistic Regression:
Relationship confidence estimation

NetworkX:
Graph analytics

LLM API:
Grounded explanation and investigation assistant

---

# 4. AI/ML PRINCIPLE

The LLM must NOT be the entire intelligence engine.

The system should use a hybrid architecture:

Data
 ↓
NLP
 ↓
NER + Rules
 ↓
Entity Resolution
 ↓
Relationship Evidence
 ↓
Confidence Model
 ↓
Knowledge Graph
 ↓
Graph Analytics
 ↓
Investigation Priority
 ↓
LLM Explanation

The graph is the source of truth.

The LLM should primarily explain retrieved evidence.

The LLM must never invent graph relationships.

---

# 5. GRAPH MODEL

## NODE TYPES

CASE
PERSON
PHONE
BANK_ACCOUNT
VEHICLE
LOCATION
ORGANIZATION

## RELATIONSHIP TYPES

INVOLVED_IN
USES
CONTACTED
OWNS
TRANSFERRED_TO
LOCATED_AT
WORKS_FOR
RELATED_TO

Each relationship should preserve:

source
target
relationship_type
confidence
evidence
case_id
detection_method

---

# 6. ENTITY RESOLUTION

The system should recognize that different representations may refer
to the same fictional entity.

Example:

+91 9876543210
9876543210
98765-43210

These may represent the same fictional phone entity.

Entity resolution may combine:

String similarity
Embedding similarity
Attribute similarity

The system must not automatically merge entities when evidence
is insufficient.

Possible decisions:

MATCH
POSSIBLE_MATCH
NO_MATCH

---

# 7. RELATIONSHIP EXTRACTION

Relationship extraction may use:

1. Deterministic rules
2. NLP evidence extraction
3. Optional LLM assistance

The LLM must NOT directly create graph edges.

Every relationship must contain evidence.

If there is insufficient evidence:

DO NOT create the relationship.

---

# 8. ML CONFIDENCE MODEL

The MVP may use a lightweight supervised model such as
Logistic Regression.

Training data:

Synthetic ground-truth relationships.

Possible features:

entity similarity
text evidence strength
relationship keyword match
supporting record count
source count
relationship frequency
cross-case connectivity

The model estimates:

"How strongly does the available evidence support this relationship?"

It must NOT estimate:

criminality
guilt
probability that someone committed a crime

---

# 9. GRAPH ANALYTICS

Implement:

Degree Centrality
Betweenness Centrality
Community Detection
Cross-Case Connectivity
Community Bridging
Relationship Diversity
Shortest Path

Use these to identify:

Potential Connectors
Potential Relationships
Investigation Priorities

---

# 10. INVESTIGATION PRIORITY

The priority score represents:

PRIORITY FOR HUMAN INVESTIGATOR REVIEW

It does NOT represent:

criminality
guilt
probability of crime

The initial explainable scoring model may use:

30% Betweenness
25% Cross-Case Connectivity
20% Community Bridging
15% Relationship Diversity
10% Evidence Confidence

All features should be normalized before combining.

The output should include:

entity
score
priority
reasons
supporting_evidence

Priority levels:

HIGH
MEDIUM
LOW

---

# 11. DATA POLICY

ALL DEMONSTRATION DATA MUST BE:

Synthetic
Fictional
Anonymized

Never use:

Real criminal records
Real police records
Real CDR data
Real banking information
Real phone records
Real addresses
Real personally identifiable information

Create synthetic ground-truth relationships for evaluation.

---

# 12. SAFETY / LANGUAGE

The application must NEVER state that a person is:

A criminal
Guilty
Responsible for a crime
A confirmed criminal-network member

Use:

Potential Relationship
Potential Connector
Analytical Lead
Investigation Priority

The system assists human investigators.

It does not make criminality or guilt decisions.

The UI must clearly display:

"SYNTHETIC DEMONSTRATION DATA"

and:

"Analytical lead only. Requires human verification."

---

# 13. FRONTEND REQUIREMENTS

The React application should contain:

Dashboard
Cases
Case Analysis
Entity Search
Network Explorer
Investigation Priority
Timeline
AI Investigation Assistant

The visual design should resemble a professional
intelligence-analysis platform.

Preferred visual direction:

Dark navy / charcoal
Clean information hierarchy
High information density
Readable typography
Subtle borders
Professional cards
Minimal animations
Clear evidence panels
Clear confidence indicators

Avoid:

Gaming-style UI
Excessive gradients
Excessive glassmorphism
Unnecessary animations
Unnecessary charts

The Network Explorer should be the visual centerpiece.

---

# 14. BACKEND REQUIREMENTS

Use FastAPI.

The backend should expose REST APIs for:

Dashboard
Cases
Case Analysis
Entity Search
Network
Related Cases
Investigation Priority
Timeline
Entity Extraction
AI Assistant

Business logic should remain inside reusable modules.

Routes should not duplicate intelligence logic.

---

# 15. DEMO MODE

The application should eventually contain three demonstration scenarios.

## Scenario 1

Discover Hidden Cross-Case Connection

Example:

CASE-001
 ↓
PERSON-017
 ↓
PHONE-004
 ↓
PERSON-043
 ↓
CASE-014

## Scenario 2

Find Potential Connector

Show a high-priority potential connector with
explainable supporting evidence.

## Scenario 3

Trace Investigation Path

Select two cases and display their shortest graph path.

All demo results must come from the actual synthetic dataset.

Never fake analytical results.

The demo must work even when the external LLM API is unavailable.

---

# 16. DEVELOPMENT PRINCIPLES

This is a SOLO developer MVP.

Prioritize:

Working functionality
Reliability
Explainability
Simple architecture
Demo quality

Do not over-engineer.

Build one module at a time.

Test each major module before continuing.

Do not rewrite working modules unnecessarily.

Do not add features without explicit approval.

---

# 17. TECHNOLOGIES NOT REQUIRED FOR MVP

Do NOT introduce:

PostgreSQL
MongoDB
Neo4j
Redis
Kubernetes
Microservices
Message queues
Cloud infrastructure
Mobile applications

unless explicitly requested later.

These may be considered for the final round.

---

# 18. FINAL ROUND FUTURE SCOPE

If the team qualifies for the final round, possible upgrades include:

Neo4j
GraphRAG
Advanced Entity Resolution
Advanced NER
Advanced Relation Extraction
Temporal Graph Analytics
Real / Anonymized Data Integration
Large-Scale Graph Processing
Role-Based Access Control
Authentication
Audit Logging
Security Hardening
Production Deployment
Real-Time Data Pipelines

These are NOT part of the current MVP.

---

# 19. DEVELOPMENT WORKFLOW

Follow:

PLAN
 ↓
IMPLEMENT
 ↓
RUN
 ↓
TEST
 ↓
FIX
 ↓
VERIFY
 ↓
NEXT MODULE

Do not implement the entire project in one step.

Before major architectural changes:

Explain the change first.

Wait for approval.

---

# 20. DEFINITION OF DONE

The MVP is considered complete when the following workflow works:

Start Application
 ↓
Dashboard
 ↓
Select CASE-001
 ↓
View entities
 ↓
Normalize entities
 ↓
Open Network Explorer
 ↓
Explore relationships
 ↓
Discover CASE-014
 ↓
Show evidence
 ↓
Identify Potential Connector
 ↓
Show Investigation Priority
 ↓
Ask AI Assistant
 ↓
Receive grounded explanation
 ↓
Show future roadmap

The complete demonstration should take less than five minutes.