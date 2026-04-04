# Databricks notebook source
# MAGIC %md
# MAGIC # ASHA Sahayak — Demo Data Setup
# MAGIC This notebook sets up the complete demo environment:
# MAGIC 1. Creates catalog and schemas
# MAGIC 2. Creates Delta tables
# MAGIC 3. Seeds demo patients, observations, and reference data
# MAGIC 4. Ingests guideline documents into the RAG index
# MAGIC 5. Runs initial risk evaluation and schedule generation

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Step 1: Create catalog and schemas
# MAGIC CREATE CATALOG IF NOT EXISTS asha_sahayak;
# MAGIC USE CATALOG asha_sahayak;
# MAGIC CREATE SCHEMA IF NOT EXISTS core;
# MAGIC CREATE SCHEMA IF NOT EXISTS clinical;
# MAGIC CREATE SCHEMA IF NOT EXISTS ops;
# MAGIC CREATE SCHEMA IF NOT EXISTS reference;
# MAGIC CREATE SCHEMA IF NOT EXISTS serving;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Run SQL DDL scripts
# MAGIC Execute the table creation scripts from `sql/002_tables.sql`

# COMMAND ----------

import sys
sys.path.insert(0, "/Workspace/Repos/asha-sahayak")

# COMMAND ----------

# Step 3: Seed demo data
from pipelines.seed_demo_data import seed_all
seed_all()
print("Demo data seeded successfully!")

# COMMAND ----------

# Step 4: Run initial risk evaluation
from services.risk_service import RiskService
from services.patient_service import PatientService

rs = RiskService()
ps = PatientService()
for p in ps.list_patients():
    patient = ps.get_patient(p.patient_id)
    if patient:
        obs = rs.get_latest_observation(patient.patient_id)
        result = rs.evaluate_patient(patient, obs)
        print(f"  {patient.full_name}: {result.risk_band.value} (score: {result.risk_score})")

# COMMAND ----------

# Step 5: Generate schedules
from services.schedule_service import ScheduleService
ss = ScheduleService()
for p in ps.list_patients():
    patient = ps.get_patient(p.patient_id)
    if patient:
        entries = ss.generate_schedule(patient)
        print(f"  {patient.full_name}: {len(entries)} schedule entries")

# COMMAND ----------

# Step 6: Generate ration recommendations
from services.ration_service import RationService
ration_svc = RationService()
for p in ps.list_patients():
    patient = ps.get_patient(p.patient_id)
    if patient:
        obs = rs.get_latest_observation(patient.patient_id)
        rec = ration_svc.generate_recommendation(patient, obs)
        print(f"  {patient.full_name}: {rec.calorie_target} cal, {len(rec.supplements)} supplements")

# COMMAND ----------

print("\n=== Demo setup complete! ===")
print(f"Total patients: {len(ps.list_patients())}")
print("You can now launch the Databricks App.")
