# Data Model — ASHA Sahayak

## Entity Relationship Overview

```
patients ──┬── observations
           ├── reports
           ├── encounters
           ├── schedules
           ├── alerts
           ├── ration_plans
           ├── appointments
           └── patient_memory_chunks

asha_workers ── patients

guidelines ── guideline_chunks

reference tables: medical_thresholds, nutrition_rules, schedule_rules, facilities
```

## Core Tables

### `core.patients`
Primary entity tracking pregnant women.

| Column | Type | Description |
|--------|------|-------------|
| patient_id | STRING PK | Unique identifier |
| asha_worker_id | STRING | Assigned ASHA worker |
| full_name | STRING | Patient name |
| age | INT | Age in years |
| village | STRING | Village name |
| phone | STRING | Contact phone |
| language_preference | STRING | ISO code (hi, en, kn, etc.) |
| lmp_date | DATE | Last menstrual period |
| edd_date | DATE | Expected delivery date |
| gestational_weeks | INT | Auto-computed |
| trimester | STRING | 1st, 2nd, 3rd |
| gravida | INT | Number of pregnancies |
| parity | INT | Number of prior births |
| known_conditions | STRING (JSON) | Array of conditions |
| current_medications | STRING (JSON) | Array of medications |
| risk_band | STRING | NORMAL, ELEVATED, HIGH_RISK, EMERGENCY |
| risk_score | DOUBLE | 0-100 composite score |

### `clinical.observations`
Clinical measurements at each visit.

| Column | Type | Description |
|--------|------|-------------|
| observation_id | STRING PK | Unique ID |
| patient_id | STRING FK | Patient reference |
| obs_date | DATE | Observation date |
| hemoglobin | DOUBLE | Hb in g/dL |
| systolic_bp | INT | Systolic BP mmHg |
| diastolic_bp | INT | Diastolic BP mmHg |
| blood_sugar_fasting | DOUBLE | Fasting glucose mg/dL |
| weight_kg | DOUBLE | Weight in kg |
| urine_protein | STRING | nil, trace, +, ++, +++ |
| fetal_movement | STRING | normal, reduced, absent |
| fetal_heart_rate | INT | FHR bpm |

### `ops.schedules`
ANC visit schedule tracking.

| Column | Type | Description |
|--------|------|-------------|
| schedule_id | STRING PK | Unique ID |
| patient_id | STRING FK | Patient reference |
| visit_type | STRING | ANC-1, PMSMA, High-Risk Monitoring |
| due_date | DATE | When the visit is due |
| tests_due | STRING (JSON) | Array of required tests |
| status | STRING | scheduled, completed, overdue, missed |
| is_pmsma_aligned | BOOLEAN | If aligned with 9th of month |
| escalation_flag | BOOLEAN | High-risk escalation |

### `ops.ration_plans`
Weekly nutrition recommendations per patient.

| Column | Type | Description |
|--------|------|-------------|
| ration_id | STRING PK | Unique ID |
| patient_id | STRING FK | Patient reference |
| calorie_target | INT | Daily calorie target |
| protein_target_g | INT | Daily protein target |
| recommendation_json | STRING (JSON) | Array of ration items |
| supplements | STRING (JSON) | Array of supplement names |
| rationale | STRING | Human-readable explanation |
| rule_basis | STRING (JSON) | Rules that generated this |

## Reference Tables

### `reference.medical_thresholds`
Normal ranges and critical thresholds for clinical values during pregnancy.

### `reference.nutrition_rules`
Trimester and condition-specific nutrition rules based on POSHAN 2.0 and MCP Card.

### `reference.schedule_rules`
ANC visit timing and required tests per pregnancy stage.

## RAG Tables

### `serving.guideline_chunks`
Embedded guideline text chunks with source metadata.

### `serving.patient_memory_chunks`
Embedded patient history (conversations, report summaries) for contextual retrieval.
