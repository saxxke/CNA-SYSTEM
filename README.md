# PS26189 — AI-Powered Criminal Network Analysis System

> Smart India Hackathon 2026 · Problem Statement 26189

**AI-assisted investigation intelligence using NLP, Entity Resolution,
Knowledge Graphs, Graph Analytics, Explainable ML and Grounded AI.**

### 🚀 Live Prototype

**[🌐 Launch Prototype](https://ps26189-frontend.onrender.com)**

**[📚 API Documentation](https://ps26189-backend-v2.onrender.com/docs)**

**[💻 GitHub Repository](https://github.com/Jit2005git/PS26189_demo)**

> 🧪 **Synthetic Demonstration Data**  
> Analytical leads require human verification.

---


---

## 📌 Project Overview

**PS26189 — AI-Powered Criminal Network Analysis System** is an internal Smart India Hackathon 2026 MVP that demonstrates how heterogeneous investigation information can be transformed into a structured and explainable network of entities and relationships.

The system combines:

- Natural Language Processing
- Named Entity Recognition
- Structured information extraction
- Entity normalization
- Embedding-based entity resolution
- Relationship extraction
- Machine-learning-based relationship confidence
- Knowledge graph construction
- Graph analytics
- Cross-case analysis
- Investigation-priority analysis
- Evidence provenance
- Explainability
- Authentication
- Role-Based Access Control
- Jurisdiction-aware authorization
- Audit logging
- Grounded AI assistance

The project is intentionally designed as a **working analytical demonstration and architectural foundation**, rather than a production law-enforcement system.

The system uses **strictly synthetic and fictional demonstration data**.

---

# 🎯 Problem Statement

Investigation information is often distributed across multiple cases, records, entities, communications, transactions, locations, organizations, and other sources.

Important connections may therefore remain difficult to identify manually.

The objective of PS26189 is to demonstrate an analytical platform capable of organizing such information into a connected intelligence layer where investigators can:

1. Search and inspect entities.
2. Discover relationships between entities.
3. Identify cross-case connections.
4. Analyze network structure.
5. Surface potential connectors.
6. Understand investigation-priority signals.
7. Trace analytical findings back to supporting synthetic records.
8. Ask natural-language questions through a grounded AI assistant.
9. Maintain authorization and audit boundaries throughout the process.

The system is intended to **assist human investigation and analysis**, not replace human judgment.

---

# 🧠 Core Design Philosophy

The entire architecture follows one central principle:

> **Graph = Source of Truth · ML = Evidence / Confidence · LLM = Explanation / Interface**

This separation is fundamental to the project.

### Graph

The knowledge graph represents the structured analytical state of the system.

It is the source of truth for:

- Entities
- Relationships
- Cases
- Cross-case connections
- Network structure
- Graph analytics

### ML

Machine learning is used to support:

- Evidence assessment
- Relationship confidence
- Entity similarity
- Analytical signals

ML does not determine guilt or criminality.

### LLM

The LLM is used as an interface and explanation layer.

It can:

- Interpret natural-language questions
- Convert questions into structured analytical requests
- Explain retrieved information
- Summarize authorized evidence

It must not:

- Create graph edges
- Invent evidence
- Change graph relationships
- Override confidence values
- Bypass authorization
- Access unauthorized information
- Determine guilt or criminality

---

# 🏗️ High-Level Architecture

```text
                 SYNTHETIC INVESTIGATION DATA
                              │
                              ▼
                     NLP PREPROCESSING
                              │
                              ▼
                 NER + STRUCTURED EXTRACTION
                              │
                              ▼
                    ENTITY NORMALIZATION
                              │
                              ▼
               EMBEDDING-BASED RESOLUTION
                              │
                              ▼
                  RELATIONSHIP EXTRACTION
                              │
                              ▼
             RELATIONSHIP EVIDENCE / ML
                              │
                              ▼
                  NETWORKX KNOWLEDGE GRAPH
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
      Graph Analytics   Cross-Case Links   Provenance
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                  INVESTIGATION PRIORITY
                              │
                              ▼
                 GROUNDED AI ASSISTANT
                              │
                              ▼
                    HUMAN REVIEW
````

---

# 🔄 End-to-End Data Flow

The complete intelligence pipeline is:

```text
Investigation Data
        ↓
NLP Preprocessing
        ↓
Entity Extraction
        ↓
Entity Normalization
        ↓
Entity Resolution
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
Evidence / Provenance
        ↓
Grounded AI Explanation
        ↓
Human Verification
```

Each stage has a defined responsibility.

The system avoids allowing one AI component to perform all tasks.

---

# 🧩 Current Technology Stack

## Frontend

| Technology   | Purpose                                 |
| ------------ | --------------------------------------- |
| React        | Component-based web application         |
| Vite         | Frontend development and build tooling  |
| Tailwind CSS | UI styling                              |
| React Router | Routing and protected routes            |
| Axios        | REST API communication                  |
| Cytoscape.js | Interactive graph/network visualization |
| Recharts     | Analytical charts and dashboards        |
| Lucide React | UI icons                                |

---

## Backend

| Technology            | Purpose                               |
| --------------------- | ------------------------------------- |
| Python                | Core backend and intelligence modules |
| FastAPI               | REST API framework                    |
| Pydantic              | Request/response validation           |
| Pandas                | Dataset processing                    |
| NetworkX              | Knowledge graph and graph analytics   |
| scikit-learn          | ML relationship-confidence model      |
| spaCy                 | NLP and Named Entity Recognition      |
| sentence-transformers | Embedding-based entity resolution     |
| python-dotenv         | Environment configuration             |
| pytest                | Automated testing                     |

---

# 🤖 AI / ML Stack

The current AI/ML architecture includes:

* spaCy
* `en_core_web_sm`
* Regex-based extraction
* Deterministic normalization
* Sentence Transformers
* `all-MiniLM-L6-v2`
* Jaro-Winkler similarity
* Logistic Regression
* NetworkX graph analytics
* Synthetic ground-truth datasets
* Grounded LLM assistance

The project has also experimented with additional ML models during controlled robustness evaluation, including:

* Random Forest
* Histogram Gradient Boosting
* Calibration approaches
* Adversarial synthetic evaluation

Experimental models are not automatically promoted into the live MVP.

---

# 🧠 NLP Pipeline

The NLP subsystem converts semi-structured or textual investigation information into structured entities and relationships.

The pipeline is:

```text
Raw Synthetic Record
        ↓
Text Preprocessing
        ↓
Named Entity Recognition
        ↓
Rule-Based Extraction
        ↓
Entity Normalization
        ↓
Entity Resolution
        ↓
Relationship Extraction
```

The architecture intentionally combines deterministic rules with ML-assisted techniques.

This provides greater control and explainability than relying entirely on an LLM.

---

# 🔎 Entity Extraction

The entity extraction layer identifies relevant entities from synthetic investigation records.

Examples include:

* Persons
* Phones
* Bank accounts
* Vehicles
* Locations
* Organizations
* Cases

spaCy NER is combined with deterministic extraction rules.

Structured fields are preferred whenever reliable structured information is available.

---

# 🧹 Entity Normalization

Entity normalization converts different representations into consistent forms.

For example:

```text
+91 9876543210
9876543210
98765-43210
```

may be normalized into a common synthetic representation.

Normalization is especially important for:

* Phone numbers
* Names
* Entity identifiers
* Structured attributes

Normalization occurs before entity-resolution decisions.

---

# 🔍 Entity Resolution

Entity resolution determines whether different representations may refer to the same synthetic entity.

The resolver supports three decisions:

```text
MATCH
POSSIBLE_MATCH
NO_MATCH
```

The system uses similarity and evidence-based features.

The actual resolver implementation remains the source of truth for:

* Similarity calculations
* Weights
* Thresholds
* Resolution decisions

The explanation layer must use the actual resolver logic rather than inventing a separate explanation formula.

The system does not automatically merge entities when evidence is insufficient.

---

# 🔗 Relationship Extraction

The relationship-extraction layer identifies relationships between normalized entities.

Current relationship types include:

```text
INVOLVED_IN
USES
CONTACTED
OWNS
TRANSFERRED_TO
LOCATED_AT
WORKS_FOR
RELATED_TO
```

Relationships can originate from:

* Structured records
* Textual evidence
* Deterministic rules
* Extracted entities
* Relationship patterns

Every meaningful analytical relationship should be backed by available evidence.

If evidence is insufficient, the system should avoid creating unsupported relationships.

---

# 🤖 Relationship Confidence

The relationship-confidence model answers:

> **How strongly does the available evidence support this relationship?**

It does **not** answer:

* Is this person guilty?
* Is this person a criminal?
* Did this person commit a crime?
* Should enforcement action be taken?

The model is specifically focused on relationship evidence.

Current evidence-oriented features include:

```text
entity_similarity
text_evidence_strength
relationship_keyword_match
supporting_record_count
source_record_count
relationship_frequency
cross_case_connectivity
```

A lightweight supervised ML model is used because the MVP prioritizes:

* Explainability
* Controlled evaluation
* Reproducibility
* Synthetic ground truth
* Fast experimentation

---

# 📊 ML Evaluation & Benchmarking

The project includes a controlled synthetic ML evaluation pipeline.

The evaluation framework includes:

* Training/test separation
* Synthetic ground truth
* Balanced evaluation datasets
* Relationship-confidence benchmarking
* Entity-resolution benchmarking
* Robustness evaluation
* Adversarial synthetic evaluation
* Precision
* Recall
* F1 score
* ROC-AUC
* PR-AUC
* Brier score
* False-positive analysis

The project has deliberately avoided treating a single benchmark result as proof of production readiness.

The ML evaluation is intended to understand model behavior and improve evidence-confidence modeling.

---

# 🕸️ Knowledge Graph

NetworkX is currently used as the knowledge-graph engine.

The graph represents entities and relationships extracted from the synthetic dataset.

### Node Types

```text
CASE
PERSON
PHONE
BANK_ACCOUNT
VEHICLE
LOCATION
ORGANIZATION
```

### Relationship Types

```text
INVOLVED_IN
USES
CONTACTED
OWNS
TRANSFERRED_TO
LOCATED_AT
WORKS_FOR
RELATED_TO
```

---

# 🧱 Graph Relationship Structure

Graph relationships preserve structured metadata such as:

```text
source
target
relationship_type
confidence
evidence
case_id
detection_method
```

This allows the graph to remain explainable.

The graph is treated as the analytical source of truth.

---

# 📈 Graph Analytics

The graph analytics layer currently supports:

* Degree Centrality
* Betweenness Centrality
* Community Detection
* Cross-Case Connectivity
* Community Bridging
* Relationship Diversity
* Shortest Path Analysis

These signals can be used to identify:

* Potential Connectors
* Analytical Leads
* Cross-Case Connections
* Potential Relationships
* Investigation Priorities

All analytical results are intended for human verification.

---

# 🔗 Cross-Case Analysis

One of the primary goals of the system is discovering relationships that connect multiple cases.

A representative synthetic path is:

```text
CASE-001
   │
   ▼
PERSON-017
   │
   ▼
PHONE-004
   │
   ▼
PERSON-043
   │
   ▼
CASE-014
```

The system should discover such paths from the underlying graph.

The connection should not simply be hardcoded for demonstration purposes.

The investigator should be able to:

1. Identify the connection.
2. Inspect the entities.
3. Inspect supporting relationships.
4. Trace the relevant case IDs.
5. Understand the analytical significance.
6. Review the underlying synthetic evidence.

---

# 🎯 Investigation Priority

The investigation-priority system is designed to surface items that may deserve human review.

The current scoring formula is:

```text
30%  Betweenness Centrality
25%  Cross-Case Connectivity
20%  Community Bridging
15%  Relationship Diversity
10%  Evidence Confidence
```

The score represents:

> **Priority for human investigator review**

It is not:

* A guilt score
* A criminality score
* A probability of committing a crime
* An enforcement recommendation

The underlying priority algorithm should remain stable while additional explainability is built around it.

---

# 📊 Confidence Evidence Breakdown

The project distinguishes between different kinds of ML information.

### Global Model Information

Examples:

* Model coefficients
* Configured weights
* Thresholds

### Local Feature Values

Examples:

* Entity similarity
* Evidence strength
* Supporting record count
* Relationship frequency

### Local Evidence Contributions

These describe how individual signals contribute to a specific analytical result.

The preferred UI terminology is:

> **Confidence Evidence Breakdown**

This avoids presenting model output as an unexplained conclusion.

---

# 🔎 Provenance & Explainability

A major development focus of the project is making analytical results traceable.

The provenance architecture is intended to explain:

* Why a relationship exists
* Which synthetic case records support it
* Which evidence records contributed
* How the relationship was detected
* What confidence information is available
* Why a potential connector appears
* Why a priority lead receives its score
* Why an entity-resolution decision was made

The core principle is:

> **Important analytical outputs should be traceable back to the synthetic records and graph evidence that produced them.**

---

# 🧾 Provenance Architecture

The planned provenance flow is:

```text
Analytical Result
       ↓
Graph Relationship / Analytics Result
       ↓
Underlying Evidence
       ↓
Case References
       ↓
Structured Provenance
       ↓
Authorization Check
       ↓
Human-Readable Explanation
```

Provenance retrieval must respect the same authorization boundaries as the underlying investigation data.

A user should never receive provenance for a case that they are not authorized to access.

---

# 🤝 AI Investigation Assistant

The AI Investigation Assistant follows a retrieval-first architecture.

```text
User Question
      ↓
Intent / Query Interpretation
      ↓
Authorization Check
      ↓
Authorized Retrieval
      ↓
Graph + Dataset Evidence
      ↓
Structured Result
      ↓
Grounded Explanation
      ↓
Citation / Evidence Validation
      ↓
Human Review
```

---

# 🧠 Assistant Capabilities

The assistant supports analytical intents including:

```text
PERSON_SEARCH
CASE_SEARCH
PERSON_PROFILE
CASE_DETAILS
NETWORK_QUERY
RELATED_CASES
PRIORITY_EXPLANATION
GENERAL_ANALYTICAL_QUERY
CLARIFICATION_REQUIRED
```

The assistant is retrieval-first.

The LLM does not become the database.

---

# 🚫 AI Assistant Safety Boundaries

The AI assistant must not:

```text
Create graph edges             ❌
Invent evidence                ❌
Invent case IDs                ❌
Override confidence            ❌
Override authorization         ❌
Access unauthorized cases     ❌
Modify investigation data      ❌
Determine guilt                ❌
Determine criminality          ❌
```

Instead:

```text
Graph / Dataset
      ↓
Authorized Retrieval
      ↓
LLM Explanation
```

This keeps the system grounded.

---

# 🔐 Authentication

The application includes authentication using:

* Username/password login
* Password hashing
* Salted password storage
* PBKDF2-HMAC-SHA256
* Token-based authentication
* Token expiration
* Token revocation
* Protected `/me` endpoint
* Logout

The backend remains the authority for identity.

---

# 👥 Role-Based Access Control

The system currently supports four roles:

```text
CITIZEN
INVESTIGATING_OFFICER
IPS_OFFICER
HOME_MINISTRY
```

No additional role is introduced merely for convenience.

---

# 👤 Citizen Access

Citizens use dedicated citizen-safe endpoints.

Citizen access is controlled using object-level authorization.

The system maintains explicit authorization relationships between a citizen account and authorized cases.

Citizen responses intentionally exclude internal investigation information.

---

# 👮 Investigating Officer Access

Investigating Officers are subject to:

* Case assignment
* Jurisdiction
* Permission checks
* Object-level authorization

An Investigating Officer cannot access sensitive investigation information simply by knowing a case ID.

Same-jurisdiction but unassigned cases do not automatically become accessible.

Out-of-jurisdiction cases are denied.

---

# 🏛️ IPS Supervisory Access

IPS Officers have supervisory access within their configured state jurisdiction.

Capabilities can include:

* Authorized case access
* People analysis
* Network analysis
* Search
* Cross-case analytics
* Priority analysis
* Reports
* AI assistance
* Audit viewing

Supervisory access is still subject to jurisdiction boundaries.

---

# 🏢 Home Ministry Access

The Home Ministry role is intentionally restricted to strategic capabilities such as:

* Aggregated analytics
* Trends
* Regional statistics
* Strategic reporting

Home Ministry access does not automatically grant investigator-level case dossiers or investigator-only provenance.

This separation is deliberate.

---

# 🗺️ Jurisdiction-Aware Authorization

Authorization is not based only on user role.

For investigation-level access, the backend also considers:

```text
Role
+
Jurisdiction
+
Case Assignment
+
Requested Resource
+
Permission
```

The authorization model ensures that frontend manipulation cannot bypass backend access restrictions.

---

# 🔒 Server-Authoritative Authorization

The backend is always authoritative.

Client-controlled values must not be trusted as authorization claims.

Examples include:

```text
X-Role
X-Jurisdiction
URL parameters
Query parameters
Frontend role state
```

The backend resolves authorization from the authenticated server-side user context.

---

# 🧾 Audit Logging

The project includes a lightweight, thread-safe audit logging system.

Current audit event types include:

```text
AUTH_LOGIN_SUCCESS
AUTH_LOGIN_FAILURE
AUTH_LOGOUT

CASE_VIEW_DOSSIER
CASE_VIEW_GRAPH
CASE_REGISTER

PERSON_VIEW_DOSSIER
ENTITY_VIEW
FAMILY_VIEW_PROFILE

SEARCH_EXECUTE
PRIORITY_LEADS_VIEW
ASSISTANT_QUERY

CROSS_CASE_ANALYTICS_VIEW
CITIZEN_CASE_VIEW

UNAUTHORIZED_ACCESS_DENIED
```

Phase 8 additionally introduces provenance-related audit events such as:

```text
PROVENANCE_EDGE_VIEW
PROVENANCE_PRIORITY_VIEW
PROVENANCE_CONNECTOR_VIEW
PROVENANCE_ENTITY_RESOLUTION_VIEW
```

---

# 🔒 Audit Privacy

Audit logging intentionally avoids unnecessary sensitive information.

The audit system must not record:

* Passwords
* Password hashes
* Bearer tokens
* Raw AI prompts
* Raw AI responses
* Sensitive family addresses
* Full case narratives
* Sensitive evidence content

Search events record metadata rather than raw sensitive search content.

AI events record metadata such as:

* Intent
* Response state
* Question length

rather than storing the complete conversation.

---

# 💾 Audit Storage

The current MVP uses:

* Thread-safe in-memory storage
* Bounded retention
* Immutable audit records
* Read-only audit APIs

The current design is intentionally lightweight.

Future production architecture may introduce:

* Persistent storage
* Tamper-evident logs
* Cryptographic integrity
* Long-term retention
* Centralized audit infrastructure

---

# 🧪 Synthetic Data Policy

This project uses **strictly synthetic and fictional demonstration data**.

The repository must not contain real:

* Criminal records
* Police records
* CDR data
* Banking information
* Phone records
* Personal addresses
* Personally identifiable information

Synthetic data is used for:

* Development
* Testing
* Demonstration
* Benchmarking
* ML evaluation
* Graph analysis

---

# ⚠️ Synthetic Data Safety

Every analytical output should be understood as operating on fictional demonstration data.

The interface should communicate:

> **SYNTHETIC DEMONSTRATION DATA**

and:

> **Analytical lead only. Requires human verification.**

The system should use neutral terminology such as:

* Potential Relationship
* Potential Connector
* Analytical Lead
* Investigation Priority
* Confidence Evidence Breakdown

---

# 📚 Synthetic Dataset

The project has progressively expanded its synthetic dataset.

The larger development corpus includes approximately:

```text
1,250 Cases
1,000 Persons
1,800 Case-Person Links
500 Phones
450 Bank Accounts
350 Vehicles
250 Locations
150 Organizations
200 Aliases
350 Family Records
599 Communications
450 Transactions
1,000 Ground-Truth Relationship Examples
```

The dataset is designed to support:

* Cross-case connections
* Entity-resolution testing
* Relationship extraction
* ML training
* ML evaluation
* Graph analysis
* Family relationship testing
* Communication analysis
* Transaction analysis

---

# 🧪 Runtime Data

The system also supports runtime registration of synthetic:

* Cases
* Persons
* Case-person associations

Runtime data is kept separate from:

* ML training data
* ML evaluation data
* Ground truth
* Benchmark datasets

This prevents newly registered demonstration records from silently contaminating ML evaluation.

---

# 🧑‍💻 Runtime Duplicate Detection

Duplicate detection is advisory.

The system may identify potentially similar entities, but it does not automatically merge them.

This prevents a low-confidence duplicate decision from silently altering the analytical graph.

---

# 🖥️ Frontend Modules

The React application includes or is designed around:

```text
Dashboard
Case Explorer
Case Details
Person Investigation Profile
Family Explorer
Entity Search
Advanced Search
Network Visualization
Priority Leads
AI Investigation Assistant
Citizen Dashboard
Citizen Cases
IPS Supervisory Analytics
Home Ministry Dashboard
Profile
Audit Logs
Unauthorized Access
```

---

# 🎨 Frontend Architecture

The frontend is organized around:

```text
API Layer
   ↓
Authentication Context
   ↓
Protected Routes
   ↓
Role Navigation
   ↓
Page Components
   ↓
Reusable Components
```

The frontend provides role-specific experiences while leaving authorization decisions to the backend.

---

# 🧱 Repository Structure

```text
PS26189_demo/
│
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── cases.py
│   │   │   ├── citizen.py
│   │   │   ├── entities.py
│   │   │   ├── relationships.py
│   │   │   ├── search.py
│   │   │   ├── priority.py
│   │   │   ├── analytics.py
│   │   │   ├── assistant.py
│   │   │   ├── audit.py
│   │   │   └── provenance.py
│   │   │
│   │   └── dependencies.py
│   │
│   ├── modules/
│   │   ├── auth/
│   │   ├── nlp/
│   │   ├── extraction/
│   │   ├── entity_resolution/
│   │   ├── relationships/
│   │   ├── ml/
│   │   ├── graph/
│   │   ├── analytics/
│   │   ├── priority/
│   │   ├── assistant/
│   │   └── provenance/
│   │
│   ├── data/
│   │
│   ├── tests/
│   │
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── api/
│       ├── auth/
│       ├── components/
│       └── pages/
│
├── scratch/
│
├── PROJECT_RULES.md
├── .env.example
├── .gitignore
└── README.md
```

---

# 📖 PROJECT_RULES.md

The repository contains:

```text
PROJECT_RULES.md
```

This file acts as the engineering contract for the project.

It defines:

* Project objective
* MVP scope
* Architecture
* Graph model
* Relationship types
* ML principles
* Entity-resolution principles
* Priority scoring
* Safety constraints
* Authorization principles
* Testing workflow
* Future architecture

Major architectural changes should be reviewed against these rules before implementation.

---

# 🧪 Testing Strategy

The project follows incremental testing.

Testing areas include:

### Core Intelligence

* Entity extraction
* Entity normalization
* Entity resolution
* Relationship extraction
* Relationship confidence
* Graph construction
* Graph analytics
* Priority scoring

### Dataset

* Required columns
* Foreign-key validity
* Duplicate representations
* Ground-truth validity
* Cross-case connectivity
* Family relationships
* Communication references
* Transaction references

### Authentication

* Login
* Password validation
* Token validation
* Token expiry
* Token revocation
* `/me`
* Logout

### Authorization

* RBAC
* Citizen object-level authorization
* Investigation authorization
* Jurisdiction checks
* Case assignment
* Graph filtering
* Entity filtering
* Search filtering
* Priority filtering
* AI retrieval filtering

### Security

* Header spoofing protection
* URL tampering protection
* Prompt-injection isolation
* Unauthorized graph traversal prevention
* Unauthorized provenance access prevention

### Audit

* Event creation
* Event immutability
* Audit permissions
* Audit privacy
* Unauthorized access logging
* Retention behavior

---

# 🔄 Engineering Workflow

The project follows a controlled development cycle:

```text
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
REVIEW
  ↓
NEXT MODULE
```

The goal is to avoid making multiple architectural changes simultaneously without verification.

---

# 📌 Definition of Done

A major development phase should generally be considered complete only after:

* Implementation is complete
* Targeted tests pass
* Full regression tests pass
* Dataset validation passes where applicable
* Frontend build passes where applicable
* Authorization behavior is verified
* Security boundaries are verified
* Manual end-to-end behavior is checked
* Documentation is updated
* Git working tree is reviewed
* Commit is made only after verification

---

# 📈 Current Development Status

## Completed Foundation

The project has completed major foundational components including:

* Project architecture
* Synthetic data generation
* NLP preprocessing
* Entity extraction
* Entity normalization
* Entity resolution
* Relationship extraction
* Relationship-confidence ML
* NetworkX graph construction
* Graph analytics
* Investigation priority
* FastAPI backend
* React/Vite frontend
* Network visualization
* Case Explorer
* Case Details
* Person Investigation Profile
* Family Explorer
* Advanced Search
* Grounded AI Investigation Assistant
* Expanded synthetic dataset
* ML benchmarking
* ML robustness evaluation
* Runtime case/person registration

---

# 🔐 Completed Security & Governance

Implemented security phases include:

* Authentication data model
* Password hashing
* Login API
* `/me`
* Logout
* Token revocation
* Backend RBAC
* Citizen object-level authorization
* Investigation-level authorization
* Jurisdiction-aware authorization
* Officer case assignment
* Role-based frontend navigation
* Citizen portal
* IPS supervisory UI
* Home Ministry strategic UI
* Protected routes
* Unauthorized handling
* Audit logging
* Compliance viewer

---

# 🔎 Phase 8 — Explainability & Provenance

The current development roadmap focuses on making analytical results more explainable and traceable.

The Phase 8 sequence is:

```text
8A → Relationship Provenance
        ↓
8B → Priority Explanation
        ↓
8C → Connector Explanation
        ↓
8D → Entity Resolution Explanation
        ↓
8E → Grounded Assistant + Citation Validation
```

Each phase is intended to be planned, implemented, tested, reviewed, and approved independently.

---

# Phase 8A — Relationship Provenance

### Objective

Explain why a relationship appears in the graph and identify the synthetic evidence supporting it.

### Focus

* Provenance models
* Sanitized structured evidence
* Underlying case references
* Detection methods
* Confidence information
* Authorization-aware provenance
* Provenance UI
* Provenance audit events

### Status

Phase 8A has been implemented and reviewed in local development.

It is intentionally treated as a separate development checkpoint before being pushed to the public repository.

---

# Phase 8B — Priority Explanation

### Objective

Explain the existing investigation-priority score without changing the underlying scoring algorithm.

The existing formula remains:

```text
30%  Betweenness Centrality
25%  Cross-Case Connectivity
20%  Community Bridging
15%  Relationship Diversity
10%  Evidence Confidence
```

The implementation should expose:

* Actual normalized component values
* Existing score components
* Contribution of each component
* Human-readable explanation

No new weights, thresholds, or scoring formula should be introduced.

---

# Phase 8C — Connector Explanation

### Objective

Explain why a potential connector appears in analytical results.

The explanation should use actual:

* Graph structure
* Cross-case connections
* Centrality
* Community information
* Relationship evidence
* Synthetic source records

The explanation must not be invented by the LLM.

---

# Phase 8D — Entity Resolution Explanation

### Objective

Explain why two representations were classified as:

```text
MATCH
POSSIBLE_MATCH
NO_MATCH
```

The explanation must use the actual resolver's:

* Similarity calculations
* Feature values
* Weights
* Thresholds
* Normalization
* Resolution decision

No separate invented explanation formula should be introduced.

---

# Phase 8E — Grounded Assistant & Citation Validation

### Objective

Strengthen the AI assistant's grounding and evidence validation.

Planned capabilities include:

* Authorization-aware retrieval
* Structured evidence retrieval
* Grounded responses
* Evidence references
* Deterministic citation validation
* Unauthorized-data protection
* Prompt-injection isolation

The LLM remains an explanation/interface layer.

---

# 🛣️ Future Architecture

The current MVP intentionally avoids unnecessary infrastructure.

The following technologies are planned future scope.

They should **not** be interpreted as already implemented.

---

# 🗄️ Future Data & Storage

Potential future technologies:

* PostgreSQL
* Neo4j
* Redis
* Cloud object storage
* Durable evidence storage

### PostgreSQL

Potentially used for:

* Users
* Roles
* Cases
* Application metadata
* Audit records
* Configuration
* Durable runtime data

### Neo4j

Potentially used for:

* Large-scale graph storage
* Graph-native queries
* Relationship traversal
* Graph analytics
* Graph Data Science

### Redis

Potentially used for:

* Caching
* Session support
* Frequently accessed graph queries
* Background-job coordination

---

# 🕸️ Future Graph Intelligence

Potential future capabilities:

* Neo4j Graph Data Science
* GraphRAG
* Large-scale graph processing
* Temporal graph analytics
* Temporal relationship reasoning
* Advanced community detection
* Advanced bridge analysis
* Graph-based retrieval
* Multi-hop evidence reasoning

---

# 🧠 Future NLP / AI

Potential future improvements include:

* Domain-specific NER
* Fine-tuned NER models
* Advanced relation extraction
* Advanced entity resolution
* Multilingual NLP
* Better evidence ranking
* Improved retrieval pipelines
* Production-grade LLM orchestration
* GraphRAG
* Advanced citation validation
* More rigorous model evaluation

---

# 🏗️ Future Platform Architecture

As scale increases, the architecture may evolve toward:

```text
React Frontend
       ↓
API Gateway
       ↓
Authentication / Authorization
       ↓
Application Services
       ↓
┌───────────────┬────────────────┬─────────────────┐
│               │                │                 │
▼               ▼                ▼                 ▼
PostgreSQL    Neo4j            Redis          AI Services
│               │                │                 │
└───────────────┴────────────────┴─────────────────┘
                       │
                       ▼
                Analytics / ML
```

Potential infrastructure technologies:

* Docker
* Kubernetes
* Cloud infrastructure
* Background workers
* Message queues
* Distributed graph processing
* Monitoring
* Observability

These are future architecture options rather than current MVP requirements.

---

# 🔐 Future Security Architecture

Potential production security improvements:

* OIDC
* SAML
* MFA
* Enterprise identity providers
* HttpOnly Secure SameSite cookies
* Stronger secrets management
* Persistent authorization policies
* RBAC/ABAC
* Security monitoring
* Centralized audit infrastructure
* Tamper-evident audit logs
* Long-term audit retention
* Security hardening
* Compliance controls

---

# 📊 MVP vs Future Architecture

| Area                    | Current MVP                   | Future Direction                    |
| ----------------------- | ----------------------------- | ----------------------------------- |
| Frontend                | React + Vite                  | Scalable React architecture         |
| Styling                 | Tailwind CSS                  | Design system                       |
| API                     | FastAPI                       | Scalable service architecture       |
| Graph                   | NetworkX                      | Neo4j + Graph Data Science          |
| Storage                 | CSV + in-memory runtime       | PostgreSQL + durable storage        |
| Cache                   | Not required                  | Redis                               |
| NLP                     | spaCy + rules                 | Advanced/domain-specific NLP        |
| Entity Resolution       | Embeddings + similarity       | Advanced hybrid resolution          |
| Relationship Extraction | Rules + NLP                   | Advanced relation extraction        |
| ML Confidence           | scikit-learn                  | Larger validated ML pipeline        |
| LLM                     | Grounded assistant            | GraphRAG / production orchestration |
| Authentication          | MVP bearer-token architecture | OIDC/SAML + MFA                     |
| Audit                   | Bounded in-memory log         | Persistent tamper-evident audit     |
| Deployment              | Render                        | Docker / Cloud / Kubernetes         |
| Graph Processing        | Local                         | Distributed/scalable                |
| Data                    | Synthetic only                | Authorized real/anonymized data     |
| Analytics               | Graph metrics                 | Temporal and large-scale analytics  |

---

# 🚨 Safety & Scope Boundary

This repository is an **AI-assisted analytical demonstration**.

It is not a production law-enforcement system.

The system must not be represented as determining:

* Whether a person is a criminal
* Whether a person is guilty
* Whether a person committed an offense
* Whether a person should be arrested
* Whether enforcement action should be taken

Analytical outputs should be described using neutral terminology such as:

```text
Potential Relationship
Potential Connector
Analytical Lead
Investigation Priority
Confidence Evidence Breakdown
```

with:

> **Human Verification Required**

---

# 👤 Human-in-the-Loop Principle

The system is designed around:

```text
AI-Assisted Analysis
        ↓
Evidence & Explanation
        ↓
Human Review
        ↓
Human Decision
```

The system does not attempt to remove the investigator from the decision-making process.

---

# 🔒 Data Governance Principle

Future integration with real or anonymized investigation data should only occur where:

* Legally authorized
* Properly governed
* Appropriately secured
* Access-controlled
* Auditable
* Necessary for the intended use

The synthetic dataset remains the default demonstration environment.

---

# 🌍 Deployment

Current demonstration deployment:

### Frontend

```text
https://ps26189-frontend.onrender.com
```

### Backend

```text
https://ps26189-backend-v2.onrender.com
```

### Health Endpoint

```text
https://ps26189-backend-v2.onrender.com/api/health
```

### API Documentation

```text
https://ps26189-backend-v2.onrender.com/docs
```

The backend may take some time to wake after inactivity when deployed on a sleeping/free hosting tier.

For demonstrations, it is recommended to check the health endpoint before starting.

---

# 🧑‍💻 Local Development

## Requirements

Recommended:

```text
Python 3.12.x
Node.js
npm
Git
```

---

## Backend

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

### Windows

```bash
.\venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install the spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

Start the backend:

```bash
uvicorn main:app --reload
```

Backend:

```text
http://localhost:8000
```

Health:

```text
http://localhost:8000/api/health
```

Swagger:

```text
http://localhost:8000/docs
```

---

# 💻 Frontend

Navigate to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start development server:

```bash
npm run dev
```

Vite normally serves:

```text
http://localhost:5173
```

---

# ⚙️ Environment Variables

Environment-specific configuration should be stored in environment variables.

Use:

```text
.env.example
```

as the reference.

Never commit:

```text
API Keys
Passwords
Production Credentials
Bearer Tokens
Private Investigation Data
Real PII
```

---

# 📦 Installation Workflow

A typical local setup is:

```bash
git clone https://github.com/Jit2005git/PS26189_demo.git

cd PS26189_demo

cd backend
python -m venv venv
```

Activate the environment and install backend dependencies:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Then install frontend dependencies:

```bash
cd ../frontend
npm install
```

Start backend and frontend in separate terminals.

---

# 🧪 Verification Workflow

Before considering a development phase complete:

```text
1. Run targeted tests
        ↓
2. Run complete backend regression
        ↓
3. Validate synthetic dataset
        ↓
4. Build frontend
        ↓
5. Verify authentication
        ↓
6. Verify authorization
        ↓
7. Verify affected feature manually
        ↓
8. Review git diff
        ↓
9. Commit
        ↓
10. Push only after approval
```

---

# 🧭 Engineering Principles

The project follows these principles:

1. **Build one module at a time.**
2. **Preserve working functionality.**
3. **Test before moving forward.**
4. **Keep business logic inside reusable modules.**
5. **Keep the graph as the analytical source of truth.**
6. **Use ML for evidence and confidence, not guilt.**
7. **Use the LLM for grounded explanation, not graph creation.**
8. **Keep authorization server-side.**
9. **Use synthetic data throughout the demonstration.**
10. **Avoid unnecessary MVP over-engineering.**
11. **Review major architectural changes before implementation.**
12. **Prefer explainability over opaque automation.**
13. **Never expose unauthorized investigation data.**
14. **Preserve auditability of important analytical actions.**
15. **Keep future architecture separate from current implementation.**
16. **Do not change established scoring or resolver logic without architectural review.**
17. **Every major phase should pass regression testing before the next phase begins.**

---

# 🗺️ Complete Roadmap

```text
                         PS26189
                            │
                            ▼
                    FOUNDATION PHASE
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
        NLP            Entity Resolution   Relationships
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                       ML Confidence
                            │
                            ▼
                    NetworkX Knowledge Graph
                            │
                            ▼
                     GRAPH ANALYTICS
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   Cross-Case Links   Connector Analysis   Priority
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                    REACT APPLICATION
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
       Cases             Network             Search
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                     AI ASSISTANT
                            │
                            ▼
                  SECURITY & GOVERNANCE
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
       Auth              RBAC             Audit
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                  INVESTIGATION AUTHORIZATION
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      Citizen              IO                IPS
                            │
                            ▼
                       PHASE 8
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
          8A                8B                8C
    Provenance          Priority           Connector
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                       8D Entity
                       Resolution
                            │
                            ▼
                       8E Grounded
                      AI Validation
                            │
                            ▼
                   FUTURE FINAL ROUND
                            │
       ┌────────────┬───────┼────────┬────────────┐
       ▼            ▼       ▼        ▼            ▼
   PostgreSQL     Neo4j   GraphRAG  Redis      Advanced NLP
       │            │       │        │            │
       └────────────┴───────┼────────┴────────────┘
                            ▼
                    CLOUD / DOCKER
                            │
                            ▼
                       KUBERNETES
```

---

# 📅 Development Philosophy

This project is being developed incrementally rather than attempting to build the entire final architecture at once.

The approach is:

```text
MVP
 ↓
Validate
 ↓
Measure
 ↓
Explain
 ↓
Secure
 ↓
Scale
```

The current MVP intentionally prioritizes:

* Demonstrability
* Explainability
* Correctness
* Synthetic-data safety
* Authorization
* Testability
* Maintainability

Future infrastructure should be introduced only when it solves a real scalability or production requirement.

---

# 🏆 Smart India Hackathon Demonstration Focus

For the SIH demonstration, the intended story is:

```text
Fragmented Investigation Data
            ↓
        AI / NLP
            ↓
    Structured Entities
            ↓
      Entity Resolution
            ↓
       Relationships
            ↓
      Knowledge Graph
            ↓
     Cross-Case Analysis
            ↓
    Potential Connectors
            ↓
   Investigation Priority
            ↓
     Evidence Provenance
            ↓
      Grounded AI
            ↓
     Human Verification
```

The demonstration should emphasize:

* Technical depth
* Explainability
* Graph intelligence
* ML-assisted evidence assessment
* Cross-case analysis
* Secure role-based access
* Provenance
* Human-in-the-loop analysis

---

# 📌 Current Project Status

**Status:** Active Development

**Competition:** Smart India Hackathon 2026

**Problem Statement:** PS26189

**Project:** AI-Powered Criminal Network Analysis System

**Primary Architecture:**

```text
React
   +
FastAPI
   +
Python Intelligence Modules
   +
NetworkX
   +
Synthetic Data
```

**Current Development Focus:**

```text
Explainability
+
Evidence Provenance
+
Authorization
+
Auditability
+
Grounded AI Assistance
```

---

# 🔮 Final Vision

The long-term vision is to evolve the MVP into a scalable and explainable investigation-intelligence platform.

The intended future architecture is:

```text
Investigation Data
        ↓
Structured Intelligence
        ↓
Entity Resolution
        ↓
Relationship Extraction
        ↓
Knowledge Graph
        ↓
Graph Analytics
        ↓
Evidence & Provenance
        ↓
Explainable Analytical Leads
        ↓
Grounded AI Assistance
        ↓
Human Review
        ↓
Human Decision-Making
```

The central principle remains:

> **AI should assist human investigation and analysis — not replace human judgment.**

---

# 📜 License

No open-source license has currently been declared for this repository.

Until a license is added, the repository should not be assumed to grant permission to reuse, redistribute, or modify the code beyond the rights provided by applicable law and GitHub's platform terms.

---

# 👨‍💻 Project

**PS26189 — AI-Powered Criminal Network Analysis System**

**Smart India Hackathon 2026**

```text
Synthetic Data
      ·
Explainable Analytics
      ·
Knowledge Graphs
      ·
Evidence Provenance
      ·
Secure Authorization
      ·
Grounded AI
      ·
Human Verification
```

> **Graph = Source of Truth · ML = Evidence / Confidence · LLM = Explanation / Interface**

```
```
