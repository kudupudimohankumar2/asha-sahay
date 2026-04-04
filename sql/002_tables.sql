-- ASHA Sahayak: Table Definitions (Delta Lake)
USE CATALOG asha_sahayak;

-- ============================================================
-- CORE TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS core.patients (
  patient_id STRING NOT NULL,
  asha_worker_id STRING,
  full_name STRING NOT NULL,
  age INT NOT NULL,
  village STRING NOT NULL,
  phone STRING,
  consent_status STRING DEFAULT 'granted',
  language_preference STRING DEFAULT 'hi',
  lmp_date DATE,
  edd_date DATE,
  gestational_weeks INT,
  trimester STRING,
  gravida INT DEFAULT 1,
  parity INT DEFAULT 0,
  known_conditions STRING,      -- JSON array
  current_medications STRING,   -- JSON array
  blood_group STRING,
  height_cm DOUBLE,
  risk_band STRING DEFAULT 'NORMAL',
  risk_score DOUBLE DEFAULT 0.0,
  created_at TIMESTAMP DEFAULT current_timestamp(),
  updated_at TIMESTAMP DEFAULT current_timestamp(),
  CONSTRAINT pk_patients PRIMARY KEY (patient_id)
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
)
COMMENT 'Registered pregnant women managed by ASHA workers';

CREATE TABLE IF NOT EXISTS core.asha_workers (
  worker_id STRING NOT NULL,
  full_name STRING NOT NULL,
  phone STRING,
  village STRING NOT NULL,
  language STRING DEFAULT 'hi',
  CONSTRAINT pk_workers PRIMARY KEY (worker_id)
)
USING DELTA
COMMENT 'ASHA health workers';

CREATE TABLE IF NOT EXISTS core.villages (
  village_id STRING NOT NULL,
  name STRING NOT NULL,
  block STRING,
  district STRING,
  state STRING DEFAULT 'Karnataka',
  phc_name STRING,
  anganwadi_count INT DEFAULT 1,
  CONSTRAINT pk_villages PRIMARY KEY (village_id)
)
USING DELTA
COMMENT 'Village master data';

-- ============================================================
-- CLINICAL TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS clinical.observations (
  observation_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  obs_date DATE,
  hemoglobin DOUBLE,
  systolic_bp INT,
  diastolic_bp INT,
  blood_sugar_fasting DOUBLE,
  blood_sugar_pp DOUBLE,
  weight_kg DOUBLE,
  urine_protein STRING,
  urine_sugar STRING,
  edema STRING,
  fetal_movement STRING,
  fetal_heart_rate INT,
  fundal_height_cm DOUBLE,
  pallor STRING,
  source_report_id STRING,
  notes STRING,
  CONSTRAINT pk_obs PRIMARY KEY (observation_id)
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
COMMENT 'Clinical observations per visit';

CREATE TABLE IF NOT EXISTS clinical.reports (
  report_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  file_path STRING,
  file_type STRING,
  report_date DATE,
  extracted_json STRING,
  extracted_text STRING,
  extractor_confidence DOUBLE DEFAULT 0.0,
  abnormality_flags STRING,
  created_at TIMESTAMP DEFAULT current_timestamp(),
  CONSTRAINT pk_reports PRIMARY KEY (report_id)
)
USING DELTA
COMMENT 'Uploaded EHR documents and extraction results';

CREATE TABLE IF NOT EXISTS clinical.encounters (
  encounter_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  encounter_time TIMESTAMP,
  modality STRING DEFAULT 'text',
  source_language STRING DEFAULT 'hi',
  original_text STRING,
  normalized_text STRING,
  translated_text STRING,
  summary STRING,
  symptoms STRING,
  extracted_health_updates STRING,
  ai_response STRING,
  translated_response STRING,
  retrieved_chunks STRING,
  risk_snapshot STRING,
  red_flag BOOLEAN DEFAULT false,
  escalation_status STRING DEFAULT 'none',
  CONSTRAINT pk_encounters PRIMARY KEY (encounter_id)
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
COMMENT 'Conversation encounters between ASHA worker and AI';

CREATE TABLE IF NOT EXISTS clinical.medications (
  medication_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  name STRING NOT NULL,
  dosage STRING,
  frequency STRING,
  start_date DATE,
  end_date DATE,
  prescribed_by STRING,
  active BOOLEAN DEFAULT true,
  CONSTRAINT pk_meds PRIMARY KEY (medication_id)
)
USING DELTA
COMMENT 'Patient medication records';

CREATE TABLE IF NOT EXISTS clinical.patient_flags (
  flag_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  flag_type STRING,
  severity STRING,
  reason STRING,
  created_at TIMESTAMP DEFAULT current_timestamp(),
  resolved_at TIMESTAMP,
  active BOOLEAN DEFAULT true,
  CONSTRAINT pk_flags PRIMARY KEY (flag_id)
)
USING DELTA
COMMENT 'Patient clinical flags and risk markers';

-- ============================================================
-- OPERATIONAL TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS ops.schedules (
  schedule_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  visit_type STRING,
  visit_number INT,
  due_date DATE,
  suggested_slot STRING,
  facility_name STRING,
  tests_due STRING,
  status STRING DEFAULT 'scheduled',
  is_pmsma_aligned BOOLEAN DEFAULT false,
  escalation_flag BOOLEAN DEFAULT false,
  notes STRING,
  CONSTRAINT pk_schedules PRIMARY KEY (schedule_id)
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
COMMENT 'ANC visit schedules and tracking';

CREATE TABLE IF NOT EXISTS ops.alerts (
  alert_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  severity STRING,
  alert_type STRING,
  reason_codes STRING,
  message STRING,
  created_at TIMESTAMP DEFAULT current_timestamp(),
  resolved_at TIMESTAMP,
  active BOOLEAN DEFAULT true,
  CONSTRAINT pk_alerts PRIMARY KEY (alert_id)
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
COMMENT 'Risk alerts and escalation records';

CREATE TABLE IF NOT EXISTS ops.ration_plans (
  ration_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  week_start DATE,
  trimester STRING,
  calorie_target INT,
  protein_target_g INT,
  recommendation_json STRING,
  supplements STRING,
  special_adjustments STRING,
  rationale STRING,
  rule_basis STRING,
  approval_status STRING DEFAULT 'recommended',
  distributed BOOLEAN DEFAULT false,
  CONSTRAINT pk_rations PRIMARY KEY (ration_id)
)
USING DELTA
COMMENT 'Weekly ration/nutrition recommendations per patient';

CREATE TABLE IF NOT EXISTS ops.appointments (
  appointment_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  facility_name STRING,
  facility_type STRING DEFAULT 'PHC',
  scheduled_datetime TIMESTAMP,
  appointment_type STRING DEFAULT 'ANC',
  status STRING DEFAULT 'booked',
  notes STRING,
  CONSTRAINT pk_appointments PRIMARY KEY (appointment_id)
)
USING DELTA
COMMENT 'Facility appointments';

CREATE TABLE IF NOT EXISTS ops.dashboard_snapshots (
  snapshot_id STRING NOT NULL,
  village STRING,
  snapshot_date DATE,
  snapshot_type STRING DEFAULT 'daily',
  data_json STRING,
  CONSTRAINT pk_snapshots PRIMARY KEY (snapshot_id)
)
USING DELTA
COMMENT 'Pre-computed dashboard summaries';

-- ============================================================
-- REFERENCE TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS reference.guidelines (
  guideline_id STRING NOT NULL,
  source_name STRING,
  category STRING,
  language STRING DEFAULT 'en',
  title STRING,
  chunk_text STRING,
  source_url STRING,
  effective_date DATE,
  CONSTRAINT pk_guidelines PRIMARY KEY (guideline_id)
)
USING DELTA
COMMENT 'Maternal health guidelines and scheme documents';

CREATE TABLE IF NOT EXISTS reference.medical_thresholds (
  threshold_id STRING NOT NULL,
  parameter_name STRING NOT NULL,
  pregnancy_stage STRING,
  normal_min DOUBLE,
  normal_max DOUBLE,
  warning_low DOUBLE,
  warning_high DOUBLE,
  critical_low DOUBLE,
  critical_high DOUBLE,
  unit STRING,
  source_ref STRING,
  CONSTRAINT pk_thresholds PRIMARY KEY (threshold_id)
)
USING DELTA
COMMENT 'Standard medical reference values for pregnancy';

CREATE TABLE IF NOT EXISTS reference.nutrition_rules (
  rule_id STRING NOT NULL,
  trimester STRING,
  condition_tag STRING,
  calorie_target INT,
  protein_target_g INT,
  iron_mg DOUBLE,
  calcium_mg DOUBLE,
  folic_acid_mg DOUBLE,
  supplement_recommendation STRING,
  food_recommendations STRING,
  foods_to_avoid STRING,
  source_ref STRING,
  CONSTRAINT pk_nutrition PRIMARY KEY (rule_id)
)
USING DELTA
COMMENT 'Nutrition and ration rules by trimester and condition';

CREATE TABLE IF NOT EXISTS reference.schedule_rules (
  rule_id STRING NOT NULL,
  pregnancy_stage STRING,
  visit_type STRING,
  visit_number INT,
  week_start INT,
  week_end INT,
  tests_due STRING,
  interval_days INT DEFAULT 28,
  escalation_condition STRING,
  source_ref STRING,
  CONSTRAINT pk_sched_rules PRIMARY KEY (rule_id)
)
USING DELTA
COMMENT 'ANC visit scheduling rules';

CREATE TABLE IF NOT EXISTS reference.facilities (
  facility_id STRING NOT NULL,
  name STRING NOT NULL,
  facility_type STRING DEFAULT 'PHC',
  village STRING,
  district STRING,
  phone STRING,
  available_slots STRING,
  CONSTRAINT pk_facilities PRIMARY KEY (facility_id)
)
USING DELTA
COMMENT 'Healthcare facilities for referrals';

-- ============================================================
-- SERVING / RAG TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS serving.guideline_chunks (
  chunk_id STRING NOT NULL,
  guideline_id STRING,
  chunk_index INT,
  chunk_text STRING,
  source_name STRING,
  category STRING,
  embedding ARRAY<FLOAT>,
  CONSTRAINT pk_g_chunks PRIMARY KEY (chunk_id)
)
USING DELTA
COMMENT 'Embedded guideline chunks for vector search';

CREATE TABLE IF NOT EXISTS serving.patient_memory_chunks (
  chunk_id STRING NOT NULL,
  patient_id STRING,
  chunk_type STRING,
  chunk_text STRING,
  source_date DATE,
  embedding ARRAY<FLOAT>,
  CONSTRAINT pk_p_chunks PRIMARY KEY (chunk_id)
)
USING DELTA
COMMENT 'Embedded patient memory chunks for contextual retrieval';

CREATE TABLE IF NOT EXISTS serving.retrieval_logs (
  log_id STRING NOT NULL,
  query_text STRING,
  patient_id STRING,
  retrieved_chunk_ids STRING,
  scores STRING,
  retrieval_time_ms INT,
  timestamp TIMESTAMP DEFAULT current_timestamp(),
  CONSTRAINT pk_ret_logs PRIMARY KEY (log_id)
)
USING DELTA
COMMENT 'RAG retrieval audit trail';

CREATE TABLE IF NOT EXISTS serving.model_audit_logs (
  log_id STRING NOT NULL,
  provider STRING,
  model_name STRING,
  input_tokens INT,
  output_tokens INT,
  latency_ms INT,
  action STRING,
  patient_id STRING,
  timestamp TIMESTAMP DEFAULT current_timestamp(),
  CONSTRAINT pk_model_logs PRIMARY KEY (log_id)
)
USING DELTA
COMMENT 'AI model invocation audit trail';
