# Databricks notebook source
# MAGIC %md
# MAGIC # ASHA Sahayak — Demo Validation
# MAGIC Validates all three demo scenarios end-to-end.

# COMMAND ----------

import sys
sys.path.insert(0, "/Workspace/Repos/asha-sahayak")

from services.patient_service import PatientService
from services.risk_service import RiskService
from services.schedule_service import ScheduleService
from services.ration_service import RationService
from services.conversation_service import ConversationService
from services.dashboard_service import DashboardService

ps = PatientService()
rs = RiskService()
ss = ScheduleService()
ration_svc = RationService()
conv_svc = ConversationService()
dash_svc = DashboardService()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Scenario 1: Normal Pregnancy — Lakshmi Devi

# COMMAND ----------

p1 = ps.get_patient("demo-patient-001")
assert p1 is not None, "Patient 001 not found"
print(f"Patient: {p1.full_name}, Age: {p1.age}, Week: {p1.gestational_weeks}, Trimester: {p1.trimester}")

obs1 = rs.get_latest_observation(p1.patient_id)
risk1 = rs.evaluate_patient(p1, obs1)
print(f"Risk: {risk1.risk_band.value}, Score: {risk1.risk_score}, Rules: {len(risk1.triggered_rules)}")
assert risk1.risk_band.value == "NORMAL", f"Expected NORMAL, got {risk1.risk_band.value}"

sched1 = ss.get_patient_schedule(p1.patient_id)
print(f"Schedule entries: {len(sched1)}")

ration1 = ration_svc.generate_recommendation(p1, obs1)
print(f"Ration: {ration1.calorie_target} cal, {len(ration1.ration_items)} items")

print("Scenario 1: PASSED")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Scenario 2: Moderate Anemia — Priya Sharma

# COMMAND ----------

p2 = ps.get_patient("demo-patient-002")
assert p2 is not None
print(f"Patient: {p2.full_name}, Age: {p2.age}")

obs2 = rs.get_latest_observation(p2.patient_id)
risk2 = rs.evaluate_patient(p2, obs2)
print(f"Risk: {risk2.risk_band.value}, Score: {risk2.risk_score}")
print(f"Triggered rules: {[r['name'] for r in risk2.triggered_rules]}")
assert risk2.risk_band.value == "ELEVATED", f"Expected ELEVATED, got {risk2.risk_band.value}"
assert any("Anemia" in r["name"] for r in risk2.triggered_rules)

ration2 = ration_svc.generate_recommendation(p2, obs2)
assert any("IFA" in s and "2" in s for s in ration2.supplements), "Should have double IFA"
print(f"Supplements: {ration2.supplements}")

print("Scenario 2: PASSED")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Scenario 3: High-Risk Urgent — Meena Kumari

# COMMAND ----------

p3 = ps.get_patient("demo-patient-003")
assert p3 is not None
print(f"Patient: {p3.full_name}, Age: {p3.age}, Conditions: {p3.known_conditions}")

obs3 = rs.get_latest_observation(p3.patient_id)
risk3 = rs.evaluate_patient(p3, obs3)
print(f"Risk: {risk3.risk_band.value}, Score: {risk3.risk_score}")
print(f"Triggered rules: {[r['name'] for r in risk3.triggered_rules]}")
assert risk3.risk_band.value in ("HIGH_RISK", "EMERGENCY")
assert len(risk3.triggered_rules) >= 2

print("Scenario 3: PASSED")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate AI Chat

# COMMAND ----------

result = conv_svc.process_message(
    patient_id="demo-patient-002",
    text="Her hemoglobin is low. What should we do?",
    source_language="en",
)
print(f"AI Response: {result['ai_response'][:200]}...")
assert len(result["ai_response"]) > 50
print("Chat test: PASSED")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate Dashboard

# COMMAND ----------

dashboard = dash_svc.get_village_dashboard("Hosahalli")
print(f"Total patients: {dashboard['summary']['total_active_patients']}")
print(f"High risk: {len(dashboard['high_risk_patients'])}")
print(f"Active alerts: {len(dashboard['active_alerts'])}")
assert dashboard["summary"]["total_active_patients"] >= 5
print("Dashboard test: PASSED")

# COMMAND ----------

print("\n" + "="*50)
print("ALL DEMO SCENARIOS VALIDATED SUCCESSFULLY")
print("="*50)
