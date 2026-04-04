# ASHA Sahayak (आशा सहायक)

**AI-powered multilingual maternal health assistant for ASHA workers in India**

Built for the [BharatBricks Hackathon](https://bharatbricks.org) with Databricks.

---

## What It Does

ASHA Sahayak is a Databricks-first AI copilot that helps ASHA (Accredited Social Health Activist) workers manage pregnant women's health. It unifies patient profiles, uploaded EHRs, prior conversations, government guidelines, and scheme-aligned nutrition guidance into one explainable AI workflow.

### Key Features

| Feature | Description |
|---------|-------------|
| **Patient Profiles** | Register pregnant women with auto-computed gestational weeks, trimester, EDD |
| **EHR Upload & OCR** | Upload PDF/image reports, auto-extract hemoglobin, BP, blood sugar, abnormalities |
| **Multilingual AI Chat** | Interact in 10+ Indian languages via text, audio, or image |
| **Patient-Aware RAG** | Grounded responses from guidelines + patient history with evidence citations |
| **Risk Detection** | 16 deterministic rules from MCP Card & Safe Motherhood Booklet |
| **Ration Planning** | POSHAN 2.0 / Saksham-aligned nutrition recommendations with rationale |
| **ANC Scheduling** | Full ANC schedule with PMSMA 9th-of-month alignment |
| **Village Dashboard** | Operational planning: risk queue, today's visits, ration aggregation |

### Design Principles

- **Assistive, not autonomous** — recommends actions with evidence, never replaces clinicians
- **Explainable** — every output includes rule basis, evidence, and source references
- **Multilingual by default** — supports Hindi, Kannada, Telugu, Tamil, and 7 more languages
- **Databricks-native** — Delta Lake, Unity Catalog, Vector Search, Jobs, Databricks App
- **India-built AI** — uses Sarvam AI (sarvam-m, saaras:v3, sarvam-translate) for reasoning, STT, and translation

---

## Architecture

```
Databricks App (Gradio, mobile-first)
    ↓
Service Layer (Patient, Risk, Ration, Schedule, Chat, Dashboard)
    ↓
AI Provider Layer (Translation, Speech, Vision, Embeddings, Reasoning)
    ↓
Databricks Lakehouse (Delta Lake, Vector Search, Jobs)
```

See [docs/architecture.md](docs/architecture.md) for full details.

---

## Quick Start

### Prerequisites

- Python 3.10+
- `pip install -r requirements.txt`
- (Optional) Sarvam AI API key for real AI providers

### 1. Generate Synthetic Data & Launch

```bash
cd asha-sahayak

# Install dependencies
pip install -r requirements.txt

# Generate production-grade synthetic data (30 patients, 82 observations, 12 facilities)
python -m tools.generate_all

# Launch the app
python app/main.py
```

Open http://localhost:8080. The app auto-detects synthetic data and populates the database on first launch.

### 2. Enable Real AI Providers (Optional)

```bash
# Copy the example env file and add your Sarvam API key
cp .env.example .env
# Edit .env: set SARVAM_API_KEY=your_key_here
```

Without an API key, mock providers are used — all features work with simulated responses.

### 3. Run Tests

```bash
pytest tests/ -v
```

53 tests covering patient CRUD, risk engine (16 rules), scheduling, ration planning, RAG grounding, and dashboard.

### Databricks Deployment

1. Import repo into Databricks Workspace
2. Run `notebooks/setup_demo_data.py` to set up Delta tables
3. Run `notebooks/create_vector_index.py` to create Vector Search indexes
4. Deploy app: `databricks bundle deploy`
5. See [docs/deployment.md](docs/deployment.md) for full steps

---

## Synthetic Data & Production Transition

The `tools/` folder generates production-grade synthetic data:

| Dataset | Count | Description |
|---------|-------|-------------|
| Patients | 30 | Across 3 villages (Hosahalli, Kuppam, Arjunpur) with varied demographics |
| Observations | 82 | Longitudinal vitals history per patient, realistic value ranges |
| ASHA Workers | 3 | One per village, multilingual (Kannada, Hindi, Telugu) |
| Facilities | 12 | PHC, CHC, DH, FRU, AWC across all villages |
| EHR Reports | 5 | Text-format antenatal reports (normal, anemia, PIH, adolescent, GDM) |
| Reference Docs | 5 | ANC guidelines, danger signs, nutrition, PMSMA, risk protocols |

**Risk distribution**: ~40% normal, ~20% mild anemia, ~10% moderate anemia, ~10% hypertensive, ~10% high-risk, ~5% emergency, ~5% GDM.

**To transition to real data**: Replace `data/synthetic/*.json` with real patient exports and re-run `python -m tools.populate_production_db`. On Databricks, data moves to Delta Lake tables — see `sql/002_tables.sql`.

---

## Demo Scenarios

| # | Scenario | Shows |
|---|----------|-------|
| 1 | Normal Pregnancy | Registration, auto-computed fields, normal risk |
| 2 | Moderate Anemia | Risk detection (Hb 8.5), double IFA, nutrition adjustment |
| 3 | High-Risk PIH | Multiple risk triggers (BP 152/98, prior C-section), emergency referral |
| 4 | Adolescent Pregnancy | Age-based risk flagging, specialist referral |
| 5 | GDM | Elevated blood sugar, dietary management, Metformin |

See [docs/demo_runbook.md](docs/demo_runbook.md) for step-by-step demo instructions.

---

## Repository Structure

```
asha-sahayak/
├── app/                    # Gradio app (Databricks App entrypoint)
│   ├── main.py             # App launcher with auto-seeding
│   ├── components/         # Shared UI components
│   └── pages/              # Home, Patients, Detail, Assistant, Dashboard
├── services/               # Business logic layer
│   ├── patient_service.py  # Patient CRUD
│   ├── risk_service.py     # Hybrid risk engine (16 rules)
│   ├── ration_service.py   # Nutrition recommendation engine
│   ├── schedule_service.py # ANC scheduling engine
│   ├── conversation_service.py  # Multilingual RAG chat
│   ├── document_service.py # EHR upload & extraction
│   ├── retrieval_service.py # FAISS/Vector Search retriever
│   ├── dashboard_service.py # Village aggregation
│   └── db.py               # Database abstraction (SQLite local / Delta production)
├── providers/              # AI provider abstractions
│   ├── base.py             # Abstract interfaces
│   ├── config.py           # Provider factory + env-driven selection
│   ├── translation/        # Mock + Sarvam Translate
│   ├── speech/             # Mock + Sarvam STT (saaras:v3)
│   ├── vision/             # Mock + pytesseract + Sarvam Vision
│   ├── embeddings/         # Mock + multilingual-e5-small
│   └── reasoning/          # Mock + Sarvam-m + Databricks FM
├── models/                 # Pydantic data models
├── pipelines/              # Databricks Jobs / batch pipelines
│   ├── seed_demo_data.py   # Demo data seeder
│   ├── ingest_guidelines.py # Guideline RAG ingestion
│   ├── daily_refresh.py    # Daily risk + schedule refresh
│   └── weekly_summary.py   # Weekly ration aggregation
├── tools/                  # Synthetic data generation & DB population
│   ├── generate_all.py     # Master script: generate + populate
│   ├── generate_synthetic_data.py  # Patients, observations, facilities
│   ├── generate_sample_ehrs.py     # Sample EHR text files
│   └── populate_production_db.py   # Load synthetic data into database
├── sql/                    # Delta Lake DDL scripts
├── notebooks/              # Databricks setup notebooks
├── tests/                  # pytest test suite (53 tests)
├── data/
│   ├── sample_reference/   # Maternal health guideline documents
│   ├── synthetic/          # Generated patient/observation JSON (gitignored)
│   ├── sample_ehr/         # Generated EHR text files (gitignored)
│   └── seed/               # Minimal demo seed data
├── docs/                   # Architecture, data model, API, deployment
├── config/
│   ├── app_config.yaml     # Application configuration
│   └── providers.example.yaml  # Provider API key template
├── .env.example            # Environment variable template
├── .gitignore
├── databricks.yml          # Databricks Asset Bundle
└── requirements.txt
```

---

## Data Model

5 schemas, 20+ tables organized under Unity Catalog:

- **core**: patients, asha_workers, villages
- **clinical**: observations, reports, encounters, medications
- **ops**: schedules, alerts, ration_plans, appointments, dashboard_snapshots
- **reference**: guidelines, medical_thresholds, nutrition_rules, schedule_rules
- **serving**: guideline_chunks, patient_memory_chunks, retrieval_logs

See [docs/data_model.md](docs/data_model.md) for full schema details.

---

## Risk Engine

16 deterministic rules derived from the **MCP Card 2018** and **Safe Motherhood Booklet**:

| Category | Examples | Classification |
|----------|----------|----------------|
| Lab | Severe anemia (Hb < 7), Moderate anemia (Hb 7-10) | EMERGENCY / ELEVATED |
| Vitals | Severe hypertension (BP > 160/110), PIH (BP > 140/90) | EMERGENCY / HIGH_RISK |
| Symptoms | Vaginal bleeding, Convulsions, Reduced fetal movement | EMERGENCY |
| Demographics | Adolescent (< 18), Advanced age (> 35) | HIGH_RISK |
| History | Prior C-section, Stillbirth | HIGH_RISK |

Each evaluation returns: risk_band, risk_score, triggered_rules, reason_codes, next_action, emergency_flag.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Gradio (mobile-first, Databricks App) |
| Backend | Python 3.10+ |
| Data | Delta Lake, Unity Catalog |
| Retrieval | Databricks Vector Search + FAISS fallback |
| Reasoning | Sarvam AI sarvam-m (India-built LLM) |
| Translation | Sarvam Translate v1 |
| Speech-to-Text | Sarvam saaras:v3 |
| OCR | pytesseract (local) / Sarvam Vision |
| Embeddings | intfloat/multilingual-e5-small |
| Jobs | Databricks Workflows |
| Testing | pytest (53 tests) |

---

## Government Scheme Alignment

- **PMSMA**: 9th-of-month checkup scheduling
- **POSHAN 2.0 / Saksham**: Nutrition and ration recommendations
- **MCP Card 2018**: Risk thresholds and ANC protocols
- **JSSK**: Free entitlements awareness
- **JSY / PMMVY**: Scheme eligibility tracking

---

## Limitations & Future Work

### Current Limitations
- Single-user demo (no multi-tenant auth yet)
- FAISS used instead of Databricks Vector Search in local mode
- No production ABDM/Aadhaar integration
- OCR accuracy depends on report quality

### Future Work
- ML-based risk scoring to complement deterministic rules
- WhatsApp/SMS notification integration
- Offline-capable mobile app wrapper
- Postnatal and neonatal workflows
- ABDM Health ID integration
- Multi-district scalability

---

## License

Built for the BharatBricks Hackathon by IISc Bengaluru.
