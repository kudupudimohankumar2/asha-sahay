# Demo Runbook — ASHA Sahayak

## Pre-Demo Setup

### Option A: Local Demo (Recommended for testing)
```bash
cd asha-sahayak
pip install -r requirements.txt
python app/main.py
```
Open http://localhost:8080 in a browser. Demo data auto-seeds on first run.

### Option B: Databricks Deployment
1. Import repo into Databricks workspace
2. Run `notebooks/setup_demo_data.py`
3. Deploy as Databricks App

## Demo Scenarios

### Scenario 1: New Registration + Normal Pregnancy

**Goal**: Show patient registration, auto-computed pregnancy fields, and normal risk.

1. Go to **Patients** tab
2. Fill in:
   - Name: "Geeta Kumari"
   - Age: 24
   - Village: Hosahalli
   - LMP: 2026-02-01
   - Gravida: 1, Parity: 0
3. Click **Register Patient**
4. Show auto-computed: EDD, gestational weeks, trimester
5. Show risk band: NORMAL (green badge)

**Key points**: Instant pregnancy computation, auto-generated schedule.

### Scenario 2: Moderate Anemia Detection + Ration Guidance

**Goal**: Show risk detection from observations and personalized ration recommendation.

1. Go to **Patient Detail** tab
2. Select "Priya Sharma" (demo patient with Hb 8.5)
3. Click **Load** — show profile with clinical data
4. Show **Risk Assessment**: ELEVATED with "Moderate Anemia" rule triggered
5. Show **Ration Recommendation**: Double IFA, iron-rich foods emphasized
6. Note the rule basis and source references

**Key points**: Deterministic risk rules, auditable nutrition guidance.

### Scenario 3: High-Risk Emergency Detection

**Goal**: Show emergency detection with prior C-section + elevated BP.

1. Go to **Patient Detail** tab
2. Select "Meena Kumari" (demo patient with BP 152/98, prior preeclampsia)
3. Click **Load**
4. Show **Risk Assessment**: HIGH_RISK/EMERGENCY
5. Show multiple triggered rules: hypertension, prior C-section, urine protein
6. Show emergency alert banner with referral recommendation

**Key points**: Multiple risk factors compound, clear escalation path.

### Scenario 4: Multilingual AI Chat

**Goal**: Show the conversational AI with patient-aware RAG.

1. Go to **AI Assistant** tab
2. Select any patient
3. Set language to Hindi
4. Type: "मुझे सिर दर्द हो रहा है" (I am having a headache)
5. Show translated query + grounded AI response
6. Expand **Evidence & Context** drawer
7. Show retrieved guideline chunks and triggered risk rules

**Key points**: Translation, patient-aware context, guideline-grounded response.

### Scenario 5: Report Upload + OCR

**Goal**: Show document ingestion and automatic extraction.

1. Go to **Patient Detail** tab
2. Select any patient
3. Upload a sample report image/PDF
4. Click **Process Report**
5. Show extracted findings: Hb, BP, blood sugar
6. Show abnormality flags
7. Note that observations are auto-created

**Key points**: Automatic extraction, abnormality detection, patient timeline.

### Scenario 6: Village Dashboard

**Goal**: Show operational planning view.

1. Go to **Dashboard** tab
2. Enter "Hosahalli" and click **Load Dashboard**
3. Show:
   - Village summary: total patients, risk distribution
   - High-risk queue with patient details
   - Today's scheduled visits
   - Weekly ration summary
   - Upcoming deliveries

**Key points**: One-screen operational view, risk-prioritized queue.

## Talking Points for Judges

1. **Databricks usage**: Delta tables, Unity Catalog schemas, Vector Search (FAISS fallback), Databricks Jobs, Databricks App
2. **AI centrality**: RAG retrieval, multilingual translation, risk reasoning, OCR/extraction
3. **India focus**: Sarvam AI providers, PMSMA alignment, MCP Card rules, POSHAN 2.0 nutrition
4. **Safety**: Deterministic risk rules, evidence-based responses, human-in-the-loop design
5. **Explainability**: Rule traces, evidence drawer, source citations, rationale text
