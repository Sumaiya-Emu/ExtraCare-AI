# ExtraCare AI — Validation & Demo Test Matrix

This file separates what can be verified without external API keys from what must be tested in a
live configured environment.

## A. Automated/core regression checks

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

| Scenario | Expected behavior |
|---|---|
| Empty lab extraction | Confidence = Low; verdict blocked |
| Empty product extraction | Confidence = Low; verdict blocked |
| Valid typed ingredient | OCR bypassed; confidence can show result |
| Under-18 + creatinine | Adult CKD-EPI eGFR not added |
| Pregnancy + creatinine | Adult CKD-EPI eGFR not added |
| Creatinine in clearly incompatible units | eGFR not added |
| Urine Protein = Trace | Qualitative value preserved |
| Multi-page PDF | Multiple pages render to PNG |
| Danger HbA1c + caution sodium | danger route considered first |
| UACR kidney flag | Nephrology available |
| Hepatomegaly | Hepatology/Gastroenterology available |
| Degenerative joint finding | Orthopedics available |
| Two lab reports | CareDelta reports numeric/qualitative changes |
| Celiac + gluten restriction | CareGraph shows avoid relationship |

## B. Live API scenarios to test before recording

### 1. General user, no selected disease

- Profile: adult, no chronic condition.
- Product: sample label.
- Expected:
  - app does not pretend it is personalized to a disease that was not selected;
  - relevant general complete-avoidance vs dose-dependent contexts can be disclosed when supported;
  - no unsupported numeric threshold appears.

### 2. Celiac + gluten

- Profile: Celiac Disease.
- Input: typed `Gluten` or product containing wheat/barley/rye.
- Expected:
  - fully restricted classification when supported by retrieved context;
  - evidence/source visible in Clinical View;
  - CareGraph connects Celiac → avoid → Gluten.

### 3. CKD / hypertension + sodium product

- Profile: CKD and/or Hypertension.
- Product label: visible sodium quantity.
- Expected:
  - partial/dose-dependent restriction;
  - observed label amount only if OCR actually reads it;
  - no invented daily limit;
  - Nephrology/Cardiology routing only when the generated clinical flags justify it.

### 4. Pregnancy + caffeine / cosmetic active

- Profile: adult Female + Currently pregnant.
- Input: Caffeine / skincare sample.
- Expected:
  - pregnancy context applied;
  - adult eGFR calculation disabled if a lab report is also used;
  - numeric caffeine limit appears only when retrieved evidence supplies the number.

### 5. Urinalysis + UACR

- Use `sample_urinalysis.png`.
- Expected:
  - qualitative values such as `2+`, `Trace`, `Negative` remain text;
  - UACR is extracted numerically when readable;
  - CKD/UACR reference context can be retrieved;
  - Nephrology routing can appear for significant kidney-related flags.

### 6. Written radiology report

- Use `sample_radiology_report.png`.
- Expected:
  - document type = radiology report;
  - written Findings / Impression extracted into structured findings;
  - no claim that the model read raw DICOM;
  - lifestyle/nutrition language remains association/possible contributor unless evidence supports causation.

### 7. Wrong document in wrong mode

- Upload a product label to Lab Decoder.
- Expected:
  - diagnostic OCR returns no valid diagnostic structure or low confidence;
  - app blocks a safety verdict instead of fabricating lab findings.

### 8. Blurry / unreadable input

- Use a deliberately unreadable photo.
- Expected:
  - explicit unreadability or PDF truncation blocks the verdict;
  - if no reliable structure is extracted, `Unable to assess safely`;
  - no 100/100 Safe from empty flags.

### 9. Profile change after analysis

- Run a report with one profile.
- Change chronic conditions or age.
- Expected:
  - old result is hidden;
  - UI asks for re-analysis;
  - cache key changes with the profile.

### 10. Smart cache

- Analyze the same exact input twice with the same profile.
- Expected:
  - second run loads from session cache;
  - no unnecessary repeated model calls.

### 11. CareDelta

- Analyze `sample_blood_test.png`.
- Then analyze `sample_blood_test_followup.png` without changing profile.
- Expected:
  - Timeline/Lab Decoder show direction changes;
  - CareDelta does not claim that every increase/decrease is clinically better/worse.

### 12. Disease Hub known condition

- Input: a condition with local KB backing.
- Expected:
  - lifestyle / nutrition / monitoring tabs;
  - explicit intervals only when evidence supports them;
  - source section visible;
  - Tavily status shown.

### 13. Disease Hub nonsense / symptom-only input

- Input something undefined/vague.
- Expected:
  - model should not fabricate a formal clinical protocol;
  - summary should explain limitation;
  - guidance lists should be empty or conservative.

### 14. Search unavailable

- Leave `TAVILY_API_KEY` blank.
- Expected:
  - Product Sentinel/Disease Hub still work from local RAG + LLM;
  - UI/trace reflects that live search was skipped;
  - no crash.

### 15. Missing Groq API key

- Leave `GROQ_API_KEY` blank.
- Expected:
  - UI loads;
  - OCR/AI-only analysis shows a configuration error; fully covered typed ingredient rules and local Disease Hub still run;
  - no stack trace to the user.

## C. LangSmith trace checklist

Before submission, save trace links that visibly contain:

- Router
- OCR tool
- retrieval
- Product search where relevant
- specialist agent
- deterministic risk engine
- Arbiter
- final response

A strong trace set is: Lab Decoder + Product Sentinel + Cross-Match.
