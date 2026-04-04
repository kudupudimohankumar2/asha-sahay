"""Generate production-grade synthetic patient, observation, and facility data.

Produces JSON files in data/synthetic/ that mirror real-world ASHA worker
caseloads across multiple villages.  Replace these files with real data
at actual deployment time.
"""

import json
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "data" / "synthetic"
OUT_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

# ── Name pools ───────────────────────────────────────────────────────

FIRST_NAMES = [
    "Lakshmi", "Priya", "Meena", "Sunita", "Anita", "Kavitha", "Rekha",
    "Savita", "Geeta", "Radha", "Sita", "Rani", "Padma", "Kamala",
    "Sarita", "Nirmala", "Pushpa", "Shanti", "Durga", "Rukmini",
    "Manjula", "Bhavani", "Yashodha", "Janaki", "Parvathi", "Revathi",
    "Latha", "Vimala", "Sharada", "Anusuya", "Renuka", "Girija",
    "Jayashree", "Suma", "Rajeshwari", "Tulasi", "Mahadevi", "Nagamma",
]

LAST_NAMES = [
    "Devi", "Sharma", "Kumari", "Bai", "Reddy", "Naidu", "Gowda",
    "Patil", "Yadav", "Singh", "Gupta", "Verma", "Mishra", "Das",
    "Rao", "Nair", "Pillai", "Hegde", "Shetty", "Kamath",
]

VILLAGES = [
    {"name": "Hosahalli", "district": "Bengaluru Rural", "state": "Karnataka"},
    {"name": "Kuppam", "district": "Chittoor", "state": "Andhra Pradesh"},
    {"name": "Arjunpur", "district": "Varanasi", "state": "Uttar Pradesh"},
]

ASHA_WORKERS = [
    {"worker_id": "asha-001", "full_name": "Kavitha R.", "phone": "9900112233",
     "village": "Hosahalli", "language": "kn"},
    {"worker_id": "asha-002", "full_name": "Seema Yadav", "phone": "9900112234",
     "village": "Arjunpur", "language": "hi"},
    {"worker_id": "asha-003", "full_name": "Padmavathi N.", "phone": "9900112235",
     "village": "Kuppam", "language": "te"},
]

LANG_BY_VILLAGE = {"Hosahalli": "kn", "Kuppam": "te", "Arjunpur": "hi"}

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]

CONDITIONS_POOL = [
    [], [], [], [], [], [],
    ["mild anemia"],
    ["hypothyroidism"],
    ["gestational diabetes"],
    ["previous c-section"],
    ["history of preeclampsia"],
    ["previous c-section", "history of preeclampsia"],
    ["asthma"],
    ["previous stillbirth"],
    ["epilepsy"],
]

MEDICATIONS_BASE = ["IFA tablet"]
MEDICATIONS_EXTRA = [
    [], ["Calcium tablet"],
    ["Calcium tablet", "Folic acid"],
    ["Calcium tablet", "Labetalol"],
    ["Calcium tablet", "Metformin"],
]

FACILITIES = [
    {"facility_id": "f-hos-phc", "name": "PHC Hosahalli", "facility_type": "PHC",
     "village": "Hosahalli", "district": "Bengaluru Rural", "phone": "080-12345678",
     "available_slots": ["09:00-10:00", "10:00-11:00", "11:00-12:00", "14:00-15:00", "15:00-16:00"]},
    {"facility_id": "f-hos-chc", "name": "CHC Nelamangala", "facility_type": "CHC",
     "village": "Hosahalli", "district": "Bengaluru Rural", "phone": "080-23456789",
     "available_slots": ["09:00-10:00", "10:00-11:00", "11:00-12:00"]},
    {"facility_id": "f-hos-dh", "name": "District Hospital Bengaluru Rural", "facility_type": "DH",
     "village": "Doddaballapur", "district": "Bengaluru Rural", "phone": "080-34567890",
     "available_slots": ["09:00-10:00", "10:00-11:00", "14:00-15:00"]},
    {"facility_id": "f-hos-awc", "name": "AWC-1 Hosahalli", "facility_type": "AWC",
     "village": "Hosahalli", "district": "Bengaluru Rural", "phone": "",
     "available_slots": ["09:00-12:00"]},
    {"facility_id": "f-kup-phc", "name": "PHC Kuppam", "facility_type": "PHC",
     "village": "Kuppam", "district": "Chittoor", "phone": "0877-2345678",
     "available_slots": ["09:00-10:00", "10:00-11:00", "14:00-15:00"]},
    {"facility_id": "f-kup-chc", "name": "CHC Kuppam Town", "facility_type": "CHC",
     "village": "Kuppam", "district": "Chittoor", "phone": "0877-2345679",
     "available_slots": ["09:00-11:00", "14:00-16:00"]},
    {"facility_id": "f-kup-awc", "name": "AWC-1 Kuppam", "facility_type": "AWC",
     "village": "Kuppam", "district": "Chittoor", "phone": "",
     "available_slots": ["09:00-12:00"]},
    {"facility_id": "f-arj-phc", "name": "PHC Arjunpur", "facility_type": "PHC",
     "village": "Arjunpur", "district": "Varanasi", "phone": "0542-1234567",
     "available_slots": ["09:00-10:00", "10:00-11:00", "11:00-12:00"]},
    {"facility_id": "f-arj-chc", "name": "CHC Varanasi Block", "facility_type": "CHC",
     "village": "Arjunpur", "district": "Varanasi", "phone": "0542-1234568",
     "available_slots": ["09:00-11:00", "14:00-16:00"]},
    {"facility_id": "f-arj-dh", "name": "District Hospital Varanasi", "facility_type": "DH",
     "village": "Varanasi", "district": "Varanasi", "phone": "0542-1234569",
     "available_slots": ["09:00-10:00", "10:00-11:00", "14:00-15:00", "15:00-16:00"]},
    {"facility_id": "f-arj-awc", "name": "AWC-1 Arjunpur", "facility_type": "AWC",
     "village": "Arjunpur", "district": "Varanasi", "phone": "",
     "available_slots": ["09:00-12:00"]},
    {"facility_id": "f-arj-fru", "name": "FRU BHU Varanasi", "facility_type": "FRU",
     "village": "Varanasi", "district": "Varanasi", "phone": "0542-1234570",
     "available_slots": ["24x7"]},
]

RISK_PROFILES = {
    "normal":       {"weight": 0.40, "hb_range": (11.0, 14.0), "sbp_range": (100, 125), "dbp_range": (60, 80)},
    "mild_anemia":  {"weight": 0.20, "hb_range": (9.0, 10.9), "sbp_range": (100, 125), "dbp_range": (60, 80)},
    "moderate_anemia": {"weight": 0.10, "hb_range": (7.0, 8.9), "sbp_range": (100, 125), "dbp_range": (60, 80)},
    "hypertensive": {"weight": 0.10, "hb_range": (10.0, 13.0), "sbp_range": (140, 165), "dbp_range": (90, 110)},
    "high_risk":    {"weight": 0.10, "hb_range": (8.0, 10.5), "sbp_range": (135, 158), "dbp_range": (85, 105)},
    "emergency":    {"weight": 0.05, "hb_range": (5.5, 7.0), "sbp_range": (160, 180), "dbp_range": (105, 120)},
    "gdm":          {"weight": 0.05, "hb_range": (10.5, 13.0), "sbp_range": (110, 130), "dbp_range": (70, 85)},
}

TODAY = date(2026, 4, 5)


def _pick_risk_profile() -> str:
    profiles = list(RISK_PROFILES.keys())
    weights = [RISK_PROFILES[p]["weight"] for p in profiles]
    return random.choices(profiles, weights=weights, k=1)[0]


def _gen_obs(patient_id: str, obs_date: date, profile: str, weeks: int) -> dict:
    p = RISK_PROFILES[profile]
    hb = round(random.uniform(*p["hb_range"]), 1)
    sbp = random.randint(*p["sbp_range"])
    dbp = random.randint(*p["dbp_range"])

    base_weight = random.uniform(42, 70)
    weight = round(base_weight + weeks * random.uniform(0.3, 0.6), 1)

    fbs = round(random.uniform(72, 95), 0)
    if profile == "gdm":
        fbs = round(random.uniform(110, 160), 0)

    urine_protein = random.choice(["nil"] * 8 + ["trace", "+"])
    if profile in ("hypertensive", "emergency"):
        urine_protein = random.choice(["trace", "+", "++"])

    fhr = random.randint(120, 160) if weeks >= 12 else None
    fm = "normal" if weeks >= 20 else None
    if profile == "emergency" and weeks >= 28:
        fm = random.choice(["reduced", "absent", "normal"])

    edema = None
    if profile in ("hypertensive", "high_risk", "emergency"):
        edema = random.choice([None, "mild", "present", "present"])

    pallor = None
    if hb < 9:
        pallor = "moderate" if hb >= 7 else "severe"

    notes_parts = []
    if hb < 7:
        notes_parts.append("Severe anemia. Urgent referral needed.")
    elif hb < 10:
        notes_parts.append("Moderate anemia. Double IFA advised.")
    if sbp >= 160 or dbp >= 110:
        notes_parts.append("Severe hypertension. Emergency referral.")
    elif sbp >= 140 or dbp >= 90:
        notes_parts.append("Elevated BP. Monitor closely.")
    if fbs > 126:
        notes_parts.append("Elevated fasting sugar. GDM screening needed.")
    if fm in ("reduced", "absent"):
        notes_parts.append("Reduced fetal movement. Immediate evaluation.")
    if not notes_parts:
        notes_parts.append("Routine checkup. All vitals within normal range.")

    return {
        "patient_id": patient_id,
        "obs_date": obs_date.isoformat(),
        "hemoglobin": hb,
        "systolic_bp": sbp,
        "diastolic_bp": dbp,
        "blood_sugar_fasting": fbs,
        "weight_kg": weight,
        "urine_protein": urine_protein,
        "urine_sugar": "nil",
        "fetal_movement": fm,
        "fetal_heart_rate": fhr,
        "edema": edema,
        "pallor": pallor,
        "notes": " ".join(notes_parts),
    }


def generate_patients(n: int = 30) -> list:
    patients = []
    used_names = set()

    for i in range(n):
        village_info = VILLAGES[i % len(VILLAGES)]
        village = village_info["name"]
        asha = next(a for a in ASHA_WORKERS if a["village"] == village)

        while True:
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            full = f"{first} {last}"
            if full not in used_names:
                used_names.add(full)
                break

        profile = _pick_risk_profile()

        age = random.randint(18, 35)
        if profile == "emergency" and random.random() < 0.3:
            age = random.choice([16, 17])
        elif random.random() < 0.08:
            age = random.choice([16, 17, 36, 37, 38])

        weeks_pregnant = random.randint(4, 40)
        lmp_date = TODAY - timedelta(weeks=weeks_pregnant)

        gravida = random.choices([1, 2, 3, 4], weights=[40, 35, 20, 5])[0]
        parity = max(0, gravida - 1)

        conditions = random.choice(CONDITIONS_POOL)
        if profile == "hypertensive":
            if "history of preeclampsia" not in conditions:
                conditions = conditions + ["history of preeclampsia"]
        if profile == "gdm":
            if "gestational diabetes" not in conditions:
                conditions = conditions + ["gestational diabetes"]

        meds = MEDICATIONS_BASE.copy()
        meds.extend(random.choice(MEDICATIONS_EXTRA))
        if "gestational diabetes" in conditions:
            meds.append("Metformin")
        if "history of preeclampsia" in conditions or profile == "hypertensive":
            if "Labetalol" not in meds:
                meds.append("Labetalol")
        meds = list(dict.fromkeys(meds))

        pid = f"P-{uuid.uuid4().hex[:8].upper()}"

        patients.append({
            "patient_id": pid,
            "asha_worker_id": asha["worker_id"],
            "full_name": full,
            "age": age,
            "village": village,
            "phone": f"9{random.randint(100000000, 999999999)}",
            "language_preference": LANG_BY_VILLAGE[village],
            "lmp_date": lmp_date.isoformat(),
            "gravida": gravida,
            "parity": parity,
            "known_conditions": conditions,
            "current_medications": meds,
            "blood_group": random.choice(BLOOD_GROUPS),
            "height_cm": random.randint(145, 170),
            "risk_profile": profile,
        })

    return patients


def generate_observations(patients: list) -> list:
    all_obs = []
    for pat in patients:
        lmp = date.fromisoformat(pat["lmp_date"])
        current_weeks = (TODAY - lmp).days // 7
        profile = pat.get("risk_profile", "normal")

        visit_weeks = [w for w in [8, 16, 24, 28, 32, 36, 38, 40] if w <= current_weeks]
        if not visit_weeks and current_weeks >= 4:
            visit_weeks = [current_weeks]

        for vw in visit_weeks:
            obs_date = lmp + timedelta(weeks=vw, days=random.randint(-3, 3))
            if obs_date > TODAY:
                obs_date = TODAY - timedelta(days=random.randint(1, 7))
            obs = _gen_obs(pat["patient_id"], obs_date, profile, vw)
            all_obs.append(obs)

    return all_obs


def generate_all():
    patients = generate_patients(30)
    observations = generate_observations(patients)

    patients_out = OUT_DIR / "patients.json"
    patients_out.write_text(json.dumps(patients, indent=2, ensure_ascii=False))
    print(f"  Generated {len(patients)} patients -> {patients_out}")

    obs_out = OUT_DIR / "observations.json"
    obs_out.write_text(json.dumps(observations, indent=2, ensure_ascii=False))
    print(f"  Generated {len(observations)} observations -> {obs_out}")

    workers_out = OUT_DIR / "asha_workers.json"
    workers_out.write_text(json.dumps(ASHA_WORKERS, indent=2, ensure_ascii=False))
    print(f"  Generated {len(ASHA_WORKERS)} ASHA workers -> {workers_out}")

    facilities_out = OUT_DIR / "facilities.json"
    facilities_out.write_text(json.dumps(FACILITIES, indent=2, ensure_ascii=False))
    print(f"  Generated {len(FACILITIES)} facilities -> {facilities_out}")

    return patients, observations


if __name__ == "__main__":
    print("=== Generating synthetic data ===")
    generate_all()
    print("Done.")
