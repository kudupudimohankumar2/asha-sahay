# Architecture — ASHA Sahayak

## System Architecture

```
┌─────────────────────────────────────────────────┐
│            Databricks App (Gradio)              │
│  ┌──────┐ ┌────────┐ ┌────────┐ ┌───────────┐  │
│  │ Home │ │Patients│ │  Chat  │ │ Dashboard │  │
│  └──┬───┘ └───┬────┘ └───┬────┘ └─────┬─────┘  │
└─────┼─────────┼──────────┼────────────┼─────────┘
      │         │          │            │
┌─────┴─────────┴──────────┴────────────┴─────────┐
│              Service Layer (Python)              │
│  ┌────────┐ ┌──────────┐ ┌────────┐ ┌────────┐  │
│  │Patient │ │Conversa- │ │Document│ │Dash-   │  │
│  │Service │ │tion Svc  │ │Service │ │board   │  │
│  ├────────┤ ├──────────┤ ├────────┤ ├────────┤  │
│  │Risk    │ │Retrieval │ │Ration  │ │Schedule│  │
│  │Service │ │Service   │ │Service │ │Service │  │
│  └────────┘ └──────────┘ └────────┘ └────────┘  │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│           AI / ML Provider Layer                 │
│  ┌──────────┐ ┌────────┐ ┌──────────┐           │
│  │Reasoning │ │Transla-│ │Embedding │           │
│  │(Sarvam-m)│ │tion    │ │Provider  │           │
│  ├──────────┤ ├────────┤ ├──────────┤           │
│  │Speech    │ │Vision/ │ │RAG       │           │
│  │(Sarvam)  │ │OCR     │ │Retriever │           │
│  └──────────┘ └────────┘ └──────────┘           │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────┴───────────────────────────────┐
│          Databricks Lakehouse                    │
│  ┌──────────────┐ ┌──────────────┐              │
│  │  Delta Lake   │ │   Volumes    │              │
│  │  (patients,   │ │  (PDFs,      │              │
│  │  observations,│ │   images,    │              │
│  │  schedules,   │ │   audio)     │              │
│  │  guidelines)  │ │              │              │
│  └──────────────┘ └──────────────┘              │
│  ┌──────────────┐ ┌──────────────┐              │
│  │Vector Search │ │   Jobs /     │              │
│  │(guidelines,  │ │  Workflows   │              │
│  │ pt. memory)  │ │              │              │
│  └──────────────┘ └──────────────┘              │
└─────────────────────────────────────────────────┘
```

## Key Architectural Decisions

### 1. Databricks-First
All application state lives in Delta Lake tables organized under Unity Catalog. Vector Search is the primary retrieval system with FAISS as a local fallback.

### 2. Provider Abstraction
Every AI capability (translation, speech, vision, embeddings, reasoning) is behind an abstract interface. This allows:
- Mock providers for demo/testing
- Sarvam AI as the default Indic-language provider
- Databricks FM API as fallback
- Easy addition of new providers

### 3. Hybrid Risk Engine
Deterministic rules (from MCP Card / Safe Motherhood Booklet) run first for safety. An ML-compatible scoring layer can be added later without changing the API.

### 4. RAG with Dual Indices
- **Guideline index**: maternal health guidelines, PMSMA, nutrition norms
- **Patient memory index**: conversation summaries, observation history, report extractions

### 5. Scheme-Aligned Ration Engine
Nutrition recommendations follow POSHAN 2.0 / Saksham guidelines with trimester-based baselines and condition-specific adjustments. Every recommendation includes rule basis and source references.

## Data Flow

### Patient Registration
```
ASHA Worker → Patient Form → PatientService → Delta Lake (patients)
                                  ↓
                          ScheduleService → Delta Lake (schedules)
                                  ↓
                          RiskService → Delta Lake (risk evaluation)
```

### AI Chat
```
Input (text/audio/image) → Normalize → Translate to English
    ↓
Retrieve (guidelines + patient memory) → Risk check
    ↓
Compose prompt → ReasoningProvider → Generate response
    ↓
Translate back → Store encounter → Return to ASHA worker
```

### Daily Refresh Job
```
Risk recomputation → Schedule overdue updates → Dashboard snapshots
```

## Schema Organization

| Schema | Purpose |
|--------|---------|
| `core` | Patients, ASHA workers, villages |
| `clinical` | Observations, reports, encounters, medications |
| `ops` | Schedules, alerts, ration plans, appointments |
| `reference` | Guidelines, thresholds, nutrition/schedule rules |
| `serving` | Guideline/patient chunks, retrieval logs, model audit |
