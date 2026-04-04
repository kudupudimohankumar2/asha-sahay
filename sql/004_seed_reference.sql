-- ASHA Sahayak: Seed Reference Data
USE CATALOG asha_sahayak;

-- ============================================================
-- MEDICAL THRESHOLDS (from MCP Card & Safe Motherhood Booklet)
-- ============================================================

INSERT INTO reference.medical_thresholds VALUES
  ('t001', 'hemoglobin', 'all', 11.0, 15.0, 10.0, NULL, 7.0, NULL, 'g/dL', 'MCP Card 2018'),
  ('t002', 'systolic_bp', 'all', 90, 120, NULL, 140, NULL, 160, 'mmHg', 'Safe Motherhood Booklet'),
  ('t003', 'diastolic_bp', 'all', 60, 80, NULL, 90, NULL, 110, 'mmHg', 'Safe Motherhood Booklet'),
  ('t004', 'blood_sugar_fasting', 'all', 70, 95, NULL, 126, NULL, 200, 'mg/dL', 'GDM Guidelines'),
  ('t005', 'blood_sugar_pp', 'all', 70, 140, NULL, 200, NULL, 300, 'mg/dL', 'GDM Guidelines'),
  ('t006', 'weight_gain_monthly', '2nd_3rd', 1.0, 2.0, 0.5, 3.0, NULL, NULL, 'kg/month', 'MCP Card 2018'),
  ('t007', 'fetal_heart_rate', '2nd_3rd', 120, 160, 110, 170, 100, 180, 'bpm', 'ANC Guidelines'),
  ('t008', 'total_weight_gain', 'all', 9.0, 15.0, 7.0, 18.0, NULL, NULL, 'kg', 'MCP Card 2018');

-- ============================================================
-- NUTRITION RULES (from POSHAN 2.0 / Saksham / MCP Card)
-- ============================================================

INSERT INTO reference.nutrition_rules VALUES
  ('n001', '1st', 'normal', 2200, 55, 27, 1000, 0.5,
   '["IFA 1 tablet daily", "Folic acid 5mg daily"]',
   '["Green leafy vegetables", "Whole grains", "Dal/pulses", "Milk and curd", "Seasonal fruits", "Eggs"]',
   '["Raw papaya", "Excessive caffeine", "Alcohol"]',
   'MCP Card 2018 / POSHAN 2.0'),

  ('n002', '2nd', 'normal', 2500, 65, 27, 1200, 0.5,
   '["IFA 1 tablet daily", "Calcium 2 tablets daily", "Albendazole single dose"]',
   '["Extra meal daily", "Iron-rich foods (jaggery, spinach)", "Protein (dal, eggs, paneer)", "Calcium foods (milk, curd, sesame)", "Fortified foods"]',
   '["Excessive salt", "Raw papaya", "Alcohol"]',
   'MCP Card 2018 / POSHAN 2.0'),

  ('n003', '3rd', 'normal', 2700, 75, 27, 1200, 0.5,
   '["IFA 1 tablet daily", "Calcium 2 tablets daily"]',
   '["Extra meal daily", "High protein foods", "Iron-rich foods", "Calcium-rich foods", "Variety of fruits and vegetables", "Iodised salt"]',
   '["Excessive salt", "Raw papaya", "Alcohol", "Heavy lifting"]',
   'MCP Card 2018 / POSHAN 2.0'),

  ('n004', NULL, 'anemia_moderate', 2500, 70, 54, 1200, 1.0,
   '["IFA 2 tablets daily (morning and evening)", "Vitamin C with iron", "Calcium 2 tablets daily"]',
   '["Iron-rich: jaggery, beetroot, spinach, dates", "Vitamin C: amla, lemon, orange", "Protein: eggs, fish, meat, dal"]',
   '["Tea/coffee with meals (inhibits iron absorption)"]',
   'IFA Guidelines / POSHAN 2.0'),

  ('n005', NULL, 'anemia_severe', 2500, 70, 100, 1200, 1.0,
   '["Injectable iron as prescribed", "IFA 2 tablets daily", "Urgent referral for transfusion if Hb < 5"]',
   '["Iron-rich foods at every meal", "Vitamin C with every meal", "Liver, meat if non-vegetarian"]',
   '["Tea/coffee near meals"]',
   'IFA Guidelines / Emergency Protocol'),

  ('n006', NULL, 'gdm_risk', 2200, 80, 27, 1200, 0.5,
   '["IFA 1 tablet daily", "Calcium 2 tablets daily", "Blood sugar monitoring"]',
   '["Low GI foods: whole grains, oats, brown rice", "High fiber: vegetables, dal", "Protein at every meal", "Small frequent meals"]',
   '["Refined sugar", "White rice in excess", "Sweet fruits in excess", "Processed foods"]',
   'GDM Management Guidelines'),

  ('n007', NULL, 'underweight', 2800, 80, 27, 1200, 0.5,
   '["IFA 1 tablet daily", "Calcium 2 tablets daily", "THR from Anganwadi"]',
   '["Extra helpings at meals", "Ghee/oil added to foods", "Nuts and dry fruits daily", "THR (Take Home Ration) from AWC", "Supplementary nutrition"]',
   '[]',
   'POSHAN 2.0 / Saksham');

-- ============================================================
-- SCHEDULE RULES (from MCP Card & PMSMA guidelines)
-- ============================================================

INSERT INTO reference.schedule_rules VALUES
  ('s001', '1st_trimester', 'ANC', 1, 0, 12,
   '["Registration", "Blood group and Rh", "Hemoglobin", "Urine albumin and sugar", "HIV screening", "Syphilis test", "Blood pressure", "Weight", "TT-1"]',
   84, '', 'MCP Card 2018'),

  ('s002', '2nd_trimester_early', 'ANC', 2, 14, 20,
   '["Hemoglobin", "Blood pressure", "Weight", "Urine albumin and sugar", "TT-2", "Ultrasonography", "Fetal heart rate"]',
   56, '', 'MCP Card 2018'),

  ('s003', '2nd_trimester_late', 'ANC', 3, 24, 28,
   '["Hemoglobin", "Blood pressure", "Weight", "Urine albumin and sugar", "GDM screening", "Fetal heart rate", "Abdominal examination"]',
   42, '', 'MCP Card 2018'),

  ('s004', '3rd_trimester_early', 'ANC', 4, 30, 34,
   '["Hemoglobin", "Blood pressure", "Weight", "Urine albumin and sugar", "Fetal heart rate", "Fetal position", "Abdominal examination"]',
   28, '', 'MCP Card 2018'),

  ('s005', '3rd_trimester_mid', 'ANC', 5, 34, 36,
   '["Blood pressure", "Weight", "Fetal heart rate", "Fetal position", "Abdominal examination", "Birth preparedness review"]',
   14, 'high_risk', 'MCP Card 2018'),

  ('s006', '3rd_trimester_late', 'ANC', 6, 36, 38,
   '["Blood pressure", "Weight", "Fetal heart rate", "Fetal position", "Delivery plan review"]',
   14, '', 'MCP Card 2018'),

  ('s007', 'near_term', 'ANC', 7, 38, 40,
   '["Blood pressure", "Weight", "Fetal heart rate", "Fetal position", "Signs of labour education"]',
   7, '', 'MCP Card 2018'),

  ('s008', 'pmsma', 'PMSMA', NULL, 14, 40,
   '["Full ANC checkup by doctor", "Ultrasonography if not done", "High-risk screening", "Specialist consultation if needed"]',
   30, '', 'PMSMA Guidelines');

-- ============================================================
-- FACILITIES (Demo data)
-- ============================================================

INSERT INTO reference.facilities VALUES
  ('f001', 'Gram Panchayat PHC Hosahalli', 'PHC', 'Hosahalli', 'Bengaluru Rural',
   '080-12345678', '["09:00-10:00", "10:00-11:00", "11:00-12:00", "14:00-15:00", "15:00-16:00"]'),
  ('f002', 'Community Health Centre Nelamangala', 'CHC', 'Nelamangala', 'Bengaluru Rural',
   '080-23456789', '["09:00-10:00", "10:00-11:00", "11:00-12:00"]'),
  ('f003', 'District Hospital Bengaluru Rural', 'DH', 'Doddaballapur', 'Bengaluru Rural',
   '080-34567890', '["09:00-10:00", "10:00-11:00", "14:00-15:00"]'),
  ('f004', 'Anganwadi Centre 1 - Hosahalli', 'AWC', 'Hosahalli', 'Bengaluru Rural',
   '', '["09:00-12:00"]');
