-- ASHA Sahayak: Dashboard and Reporting Views
USE CATALOG asha_sahayak;

-- Active patients with pregnancy status
CREATE OR REPLACE VIEW ops.v_active_patients AS
SELECT
  p.patient_id,
  p.full_name,
  p.age,
  p.village,
  p.trimester,
  p.gestational_weeks,
  p.edd_date,
  p.risk_band,
  p.risk_score,
  p.known_conditions,
  p.language_preference,
  p.asha_worker_id,
  CASE
    WHEN p.risk_band = 'EMERGENCY' THEN 1
    WHEN p.risk_band = 'HIGH_RISK' THEN 2
    WHEN p.risk_band = 'ELEVATED' THEN 3
    ELSE 4
  END AS risk_priority
FROM core.patients p
WHERE p.consent_status = 'granted'
ORDER BY risk_priority, p.edd_date;

-- Today's scheduled visits
CREATE OR REPLACE VIEW ops.v_todays_visits AS
SELECT
  s.schedule_id,
  s.patient_id,
  p.full_name,
  p.village,
  p.risk_band,
  p.trimester,
  s.visit_type,
  s.tests_due,
  s.facility_name,
  s.is_pmsma_aligned,
  s.escalation_flag
FROM ops.schedules s
JOIN core.patients p ON s.patient_id = p.patient_id
WHERE s.due_date = current_date()
  AND s.status = 'scheduled';

-- Overdue visits
CREATE OR REPLACE VIEW ops.v_overdue_visits AS
SELECT
  s.schedule_id,
  s.patient_id,
  p.full_name,
  p.village,
  p.risk_band,
  s.visit_type,
  s.due_date,
  datediff(current_date(), s.due_date) AS days_overdue,
  s.tests_due
FROM ops.schedules s
JOIN core.patients p ON s.patient_id = p.patient_id
WHERE s.due_date < current_date()
  AND s.status IN ('scheduled', 'overdue')
ORDER BY days_overdue DESC;

-- High-risk patient queue
CREATE OR REPLACE VIEW ops.v_high_risk_queue AS
SELECT
  p.patient_id,
  p.full_name,
  p.age,
  p.village,
  p.trimester,
  p.gestational_weeks,
  p.risk_band,
  p.risk_score,
  p.known_conditions,
  p.edd_date,
  a.alert_type,
  a.severity AS alert_severity,
  a.message AS alert_message,
  a.created_at AS alert_time
FROM core.patients p
LEFT JOIN ops.alerts a ON p.patient_id = a.patient_id AND a.active = true
WHERE p.risk_band IN ('HIGH_RISK', 'EMERGENCY')
ORDER BY
  CASE WHEN p.risk_band = 'EMERGENCY' THEN 0 ELSE 1 END,
  p.risk_score DESC;

-- Village summary statistics
CREATE OR REPLACE VIEW ops.v_village_summary AS
SELECT
  p.village,
  COUNT(*) AS total_patients,
  SUM(CASE WHEN p.trimester = '1st' THEN 1 ELSE 0 END) AS trimester_1,
  SUM(CASE WHEN p.trimester = '2nd' THEN 1 ELSE 0 END) AS trimester_2,
  SUM(CASE WHEN p.trimester = '3rd' THEN 1 ELSE 0 END) AS trimester_3,
  SUM(CASE WHEN p.risk_band = 'NORMAL' THEN 1 ELSE 0 END) AS risk_normal,
  SUM(CASE WHEN p.risk_band = 'ELEVATED' THEN 1 ELSE 0 END) AS risk_elevated,
  SUM(CASE WHEN p.risk_band = 'HIGH_RISK' THEN 1 ELSE 0 END) AS risk_high,
  SUM(CASE WHEN p.risk_band = 'EMERGENCY' THEN 1 ELSE 0 END) AS risk_emergency,
  SUM(CASE WHEN p.edd_date BETWEEN current_date() AND date_add(current_date(), 30)
      THEN 1 ELSE 0 END) AS deliveries_next_30_days
FROM core.patients p
WHERE p.consent_status = 'granted'
GROUP BY p.village;

-- Weekly ration aggregation
CREATE OR REPLACE VIEW ops.v_weekly_ration_summary AS
SELECT
  p.village,
  r.week_start,
  COUNT(*) AS beneficiary_count,
  AVG(r.calorie_target) AS avg_calorie_target,
  AVG(r.protein_target_g) AS avg_protein_target,
  r.supplements
FROM ops.ration_plans r
JOIN core.patients p ON r.patient_id = p.patient_id
GROUP BY p.village, r.week_start, r.supplements;

-- Unresolved alerts
CREATE OR REPLACE VIEW ops.v_active_alerts AS
SELECT
  a.alert_id,
  a.patient_id,
  p.full_name,
  p.village,
  a.severity,
  a.alert_type,
  a.reason_codes,
  a.message,
  a.created_at
FROM ops.alerts a
JOIN core.patients p ON a.patient_id = p.patient_id
WHERE a.active = true
ORDER BY
  CASE
    WHEN a.severity = 'EMERGENCY' THEN 0
    WHEN a.severity = 'CRITICAL' THEN 1
    WHEN a.severity = 'WARNING' THEN 2
    ELSE 3
  END,
  a.created_at DESC;

-- Latest observations per patient
CREATE OR REPLACE VIEW clinical.v_latest_observations AS
SELECT o.*
FROM clinical.observations o
INNER JOIN (
  SELECT patient_id, MAX(obs_date) AS max_date
  FROM clinical.observations
  GROUP BY patient_id
) latest ON o.patient_id = latest.patient_id AND o.obs_date = latest.max_date;
