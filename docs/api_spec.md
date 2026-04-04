# API Specification — ASHA Sahayak

The application uses a service-layer architecture rather than a REST API. All interactions go through the Gradio UI which calls Python services directly. Below are the logical API contracts.

## Patient Service

### Create Patient
- **Input**: Patient model (name, age, village, LMP, etc.)
- **Output**: Patient model with computed fields (gestational_weeks, trimester, EDD)
- **Side effects**: Creates schedule, runs initial risk evaluation

### Get Patient
- **Input**: patient_id
- **Output**: Full Patient model

### List Patients
- **Input**: Optional village filter
- **Output**: List of PatientSummary

### Update Patient
- **Input**: patient_id, update fields
- **Output**: Updated Patient model

## Conversation Service

### Process Message
- **Input**:
  - patient_id: str
  - text: Optional[str]
  - audio_bytes: Optional[bytes]
  - image_bytes: Optional[bytes]
  - source_language: str (ISO code)
  - mode: str (general, ration, risk_check, schedule)
- **Output**:
  - encounter_id: str
  - original_text: str
  - translated_query: str
  - ai_response: str
  - translated_response: str
  - retrieved_guidelines: List[dict]
  - retrieved_patient_context: List[dict]
  - risk_summary: str
  - triggered_rules: List[dict]
  - red_flag: bool
  - confidence: float

## Risk Service

### Evaluate Patient
- **Input**: Patient, Optional[Observation], Optional[List[symptoms]]
- **Output**: RiskEvaluation
  - risk_band: NORMAL | ELEVATED | HIGH_RISK | EMERGENCY
  - risk_score: float (0-100)
  - triggered_rules: List[dict]
  - reason_codes: List[str]
  - suggested_next_action: str
  - emergency_flag: bool
  - escalation_recommendation: str

## Schedule Service

### Generate Schedule
- **Input**: Patient
- **Output**: List[ScheduleEntry]

### Get Daily Task List
- **Input**: village, optional date
- **Output**: DailyTaskList (due, overdue, high-priority)

## Ration Service

### Generate Recommendation
- **Input**: Patient, Optional[Observation]
- **Output**: RationRecommendation
  - calorie_target, protein_target
  - ration_items: List[RationItem]
  - supplements: List[str]
  - rationale: str
  - rule_basis: List[str]

### Aggregate Village Rations
- **Input**: village name
- **Output**: VillageRationSummary

## Document Service

### Process Upload
- **Input**: patient_id, file_bytes, file_type
- **Output**: dict with report_id, extraction results, abnormality flags

## Dashboard Service

### Get Village Dashboard
- **Input**: village name
- **Output**: dict with summary, visits, risk queue, alerts, ration summary, deliveries
