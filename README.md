# Healthcare Intelligence Platform — Backend Core

This is the production-grade, Clean Architecture backend for the Healthcare Intelligence Platform, built using **FastAPI (Python 3.12+)**, **AuraDB (Neo4j Graph Database)**, **Clerk Authentication**, and **Sarvam AI Voice**.

---

## 🏗️ Architecture

The backend implements clean segregation of concerns following SOLID principles:

1. **Client / Gateway Layer**: FastAPI application routing (`app/api/`) protected by Clerk JWT authentication verification middleware and role-based permissions (`app/auth/`).
2. **Business Orchestration Layer**: Service layer (`app/services/`) enforcing domain validations, cross-entity rules, and transactional orchestrations.
3. **Graph Storage Repository Layer**: Database layer (`app/repositories/`) executing parameterized Cypher queries via the Neo4j Python driver.
4. **AI Operational Engine**: Statistical forecasters (`app/ai/`) calculating inventory stockouts, attendance probabilities, patient volumes, and device reliability indicators.
5. **Automation & Integration**: Automated background workflow tasks (`app/workflow/`) and Brevo email/SMS notification dispatchers (`app/notifications/`).

```
backend/
├── app/
│   ├── api/             # HTTP Route Handlers
│   ├── auth/            # Clerk Authenticator & RBAC Dependencies
│   ├── database/        # Neo4j Driver Connection Lifespans & Initializers
│   ├── repositories/    # Cypher Graph Repositories
│   ├── services/        # Orchestrations & Domain Logic
│   ├── ai/              # Statistical Forecasting predictors
│   ├── voice/           # Sarvam AI STT/TTS & Intent Parsers
│   ├── workflow/        # Scheduled Render Cron Tasks
│   ├── notifications/   # In-app alerts & Brevo dispatchers
│   ├── middleware/      # Logging & Auditing Pipelines
│   ├── schemas/         # consolidated Pydantic validation schemas
│   ├── models/          # Neo4j Entity Node definitions
│   ├── utils/           # ID & Cypher Helpers
│   ├── config/          # Environment Settings
│   └── main.py          # FastAPI Application Bootstrapper
└── tests/               # PyTest Suite
```

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory based on `.env.example`:

| Key | Description | Example |
| :--- | :--- | :--- |
| `NEO4J_URI` | AuraDB Database URI | `neo4j+s://xxxx.databases.neo4j.io` |
| `NEO4J_USER` | AuraDB login username | `neo4j` |
| `NEO4J_PASSWORD` | AuraDB password | `strong-password` |
| `CLERK_JWKS_URL` | Clerk JWKS verification URL | `https://xxxx.clerk.accounts.dev/.well-known/jwks.json` |
| `SARVAM_API_KEY` | Sarvam AI API subscription key | `xxxx-xxxx-xxxx` |
| `BREVO_API_KEY` | Brevo transaction SMS/Email key | `xkeysib-xxxx` |
| `SUPABASE_URL` | Supabase endpoint URL | `https://xxxx.supabase.co` |
| `SUPABASE_KEY` | Supabase service role secret key | `eyJhbG...` |

---

## 🚀 Setup & Execution

### 1. Install dependencies
```bash
pip install -e .[dev]
```

### 2. Run local development server
```bash
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Run test suite
```bash
pytest
```
