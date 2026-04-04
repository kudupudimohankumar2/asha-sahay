"""Generate synthetic EHR text files that simulate scanned medical reports.

These are plain-text representations of what OCR would extract from real
antenatal checkup reports. Useful for testing the vision/OCR pipeline
without needing actual scanned PDFs.
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "data" / "sample_ehr"
OUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

FACILITY_NAMES = [
    "Gram Panchayat PHC Hosahalli",
    "Community Health Centre Nelamangala",
    "PHC Kuppam",
    "District Hospital Varanasi",
    "CHC Varanasi Block",
]

DOCTORS = [
    "Dr. Ramesh Kumar", "Dr. Anjali Patil", "Dr. Suresh Gowda",
    "Dr. Meera Nair", "Dr. Vikram Singh",
]


def _report_header(facility: str, report_date: date, patient_name: str, age: int) -> str:
    return f"""{facility}
ANTENATAL CHECK-UP REPORT
{'='*50}
Date: {report_date.strftime('%d-%m-%Y')}
Patient: {patient_name}
Age: {age} years
Registration No: ANC/{random.randint(1000,9999)}/{report_date.year}
"""


def generate_normal_report(patient_name: str = "Lakshmi Devi", age: int = 24) -> str:
    d = date(2026, 3, 20)
    return _report_header(FACILITY_NAMES[0], d, patient_name, age) + f"""
VITALS:
  Blood Pressure: 118/76 mmHg
  Pulse Rate: 78 bpm
  Temperature: 98.4 F
  Weight: 58.0 kg
  Height: 155 cm

INVESTIGATIONS:
  Hemoglobin: 11.5 g/dL
  Blood Group: B+ (Rh Positive)
  Fasting Blood Sugar: 85 mg/dL
  Urine Albumin: Nil
  Urine Sugar: Nil
  HIV Screening: Negative
  VDRL: Non-Reactive
  HBsAg: Negative

OBSTETRIC EXAMINATION:
  Gestational Age: 24 weeks
  Fundal Height: 24 cm
  Fetal Heart Rate: 142 bpm
  Fetal Movement: Present, Normal
  Presentation: Cephalic
  Liquor: Adequate

IMPRESSION:
  Normal ongoing pregnancy at 24 weeks.
  All investigations within normal limits.

ADVICE:
  1. Continue IFA tablet 1 OD
  2. Continue Calcium tablet 1 BD
  3. Diet: Extra meal daily, iron-rich foods
  4. Rest: 2 hours daytime, 8 hours night
  5. Follow up: 4 weeks / earlier if danger signs
  6. Next visit: {(d + timedelta(weeks=4)).strftime('%d-%m-%Y')}

Examining Doctor: {random.choice(DOCTORS)}
"""


def generate_anemia_report(patient_name: str = "Priya Sharma", age: int = 28) -> str:
    d = date(2026, 3, 15)
    return _report_header(FACILITY_NAMES[1], d, patient_name, age) + f"""
VITALS:
  Blood Pressure: 110/72 mmHg
  Pulse Rate: 88 bpm
  Temperature: 98.6 F
  Weight: 52.0 kg
  Height: 150 cm

INVESTIGATIONS:
  Hemoglobin: 8.5 g/dL    *** LOW ***
  Blood Group: A+
  Fasting Blood Sugar: 88 mg/dL
  Urine Albumin: Nil
  Urine Sugar: Nil

OBSTETRIC EXAMINATION:
  Gestational Age: 28 weeks
  Fundal Height: 27 cm
  Fetal Heart Rate: 148 bpm
  Fetal Movement: Present, Normal

GENERAL EXAMINATION:
  Pallor: Present (moderate)
  Tongue: Pale
  Nails: Koilonychia noted
  Edema: Absent

IMPRESSION:
  1. Moderate anemia (Hb 8.5 g/dL)
  2. Otherwise normal pregnancy at 28 weeks

ADVICE:
  1. IFA tablet: Increase to 2 tablets daily (morning and evening)
  2. Calcium tablet 1 BD continue
  3. Iron-rich diet: green leafy vegetables, jaggery, dates
  4. Vitamin C with iron tablet for absorption
  5. Avoid tea/coffee with meals
  6. Repeat Hb after 4 weeks
  7. Follow up: 2 weeks
  8. Refer to PHC if Hb does not improve

Examining Doctor: {random.choice(DOCTORS)}
"""


def generate_high_risk_report(patient_name: str = "Meena Kumari", age: int = 32) -> str:
    d = date(2026, 3, 25)
    return _report_header(FACILITY_NAMES[2], d, patient_name, age) + f"""
VITALS:
  Blood Pressure: 152/98 mmHg    *** HIGH ***
  Pulse Rate: 92 bpm
  Temperature: 98.2 F
  Weight: 72.0 kg (BMI: 28.1)
  Height: 160 cm

INVESTIGATIONS:
  Hemoglobin: 9.8 g/dL
  Blood Group: O+
  Fasting Blood Sugar: 105 mg/dL
  Post Prandial Sugar: 148 mg/dL
  Urine Albumin: +    *** POSITIVE ***
  Urine Sugar: Nil
  Serum Creatinine: 0.8 mg/dL

OBSTETRIC EXAMINATION:
  Gestational Age: 32 weeks
  Fundal Height: 30 cm
  Fetal Heart Rate: 138 bpm
  Fetal Movement: Present
  Presentation: Cephalic

GENERAL EXAMINATION:
  Pallor: Mild
  Edema: Present (pedal and pretibial)
  Deep Tendon Reflexes: Brisk

OBSTETRIC HISTORY:
  G3P2L2
  Previous C-section: Yes (2023)
  History of Pre-eclampsia: Yes (2nd pregnancy)

IMPRESSION:
  1. HIGH RISK PREGNANCY
  2. Pregnancy Induced Hypertension (PIH)
  3. Proteinuria - possible Pre-eclampsia
  4. Previous Caesarean Section
  5. Mild anemia
  6. Borderline GDM

ADVICE:
  1. Labetalol 100mg BD - continue
  2. IFA tablet 2 OD
  3. Calcium 1 BD
  4. STRICT bed rest
  5. Daily BP monitoring at home
  6. Watch for danger signs: headache, blurred vision, epigastric pain
  7. Weekly follow up
  8. Delivery planning: Refer to DH for elective C-section at 37-38 weeks
  9. PMSMA visit on 9th for specialist review
  10. If BP > 160/110 or visual disturbances: GO TO HOSPITAL IMMEDIATELY

Examining Doctor: {random.choice(DOCTORS)}
"""


def generate_adolescent_report(patient_name: str = "Sunita Bai", age: int = 17) -> str:
    d = date(2026, 3, 22)
    return _report_header(FACILITY_NAMES[3], d, patient_name, age) + f"""
VITALS:
  Blood Pressure: 108/68 mmHg
  Pulse Rate: 80 bpm
  Temperature: 98.4 F
  Weight: 45.0 kg    *** LOW ***
  Height: 148 cm (BMI: 20.5)

INVESTIGATIONS:
  Hemoglobin: 10.5 g/dL
  Blood Group: B+
  Fasting Blood Sugar: 78 mg/dL
  Urine Albumin: Nil
  Urine Sugar: Nil

OBSTETRIC EXAMINATION:
  Gestational Age: 24 weeks (Primigravida)
  Fundal Height: 22 cm
  Fetal Heart Rate: 146 bpm
  Fetal Movement: Present

NOTE: ADOLESCENT PREGNANCY (Age 17 years)
  - Increased risk of preterm delivery
  - Increased risk of low birth weight
  - Requires specialist consultation
  - Nutritional counselling critical
  - Psychosocial support needed

ADVICE:
  1. IFA tablet 1 OD
  2. Calcium 1 BD
  3. Folic acid supplementation
  4. HIGH PROTEIN, HIGH CALORIE DIET
  5. Supplementary nutrition from Anganwadi (THR)
  6. Specialist consultation at CHC
  7. Counselling: birth preparedness, danger signs
  8. Follow up: 2 weeks
  9. PMSMA visit for specialist review

Examining Doctor: {random.choice(DOCTORS)}
"""


def generate_gdm_report(patient_name: str = "Rajeshwari Rao", age: int = 30) -> str:
    d = date(2026, 3, 18)
    return _report_header(FACILITY_NAMES[4], d, patient_name, age) + f"""
VITALS:
  Blood Pressure: 122/78 mmHg
  Pulse Rate: 82 bpm
  Weight: 68.0 kg
  Height: 158 cm

INVESTIGATIONS:
  Hemoglobin: 11.8 g/dL
  Blood Group: A+
  Fasting Blood Sugar: 132 mg/dL    *** HIGH ***
  75g OGTT 2hr: 178 mg/dL    *** HIGH ***
  HbA1c: 6.4%
  Urine Albumin: Nil
  Urine Sugar: +

OBSTETRIC EXAMINATION:
  Gestational Age: 30 weeks
  Fundal Height: 32 cm (large for dates)
  Fetal Heart Rate: 152 bpm
  Fetal Movement: Present, active

IMPRESSION:
  1. Gestational Diabetes Mellitus (GDM)
  2. Large for gestational age
  3. Otherwise healthy pregnancy

ADVICE:
  1. Dietary modification: Low GI foods, whole grains
  2. Small frequent meals (6 per day)
  3. Avoid refined sugar, excess rice
  4. Walking 30 min after meals
  5. Metformin 500mg BD - started
  6. Blood sugar monitoring: fasting and 2hr PP weekly
  7. Growth scan at 32 weeks
  8. Weekly monitoring from 34 weeks
  9. Follow up: 1 week with sugar log
  10. Delivery planning: by 38-39 weeks

Examining Doctor: {random.choice(DOCTORS)}
"""


def generate_all():
    reports = {
        "normal_anc_report.txt": generate_normal_report(),
        "anemia_report.txt": generate_anemia_report(),
        "high_risk_pih_report.txt": generate_high_risk_report(),
        "adolescent_report.txt": generate_adolescent_report(),
        "gdm_report.txt": generate_gdm_report(),
    }

    for filename, content in reports.items():
        path = OUT_DIR / filename
        path.write_text(content, encoding="utf-8")
        print(f"  Generated EHR: {path}")

    return reports


if __name__ == "__main__":
    print("=== Generating sample EHR files ===")
    generate_all()
    print("Done.")
