# Clinical Safety Design

ExtraCare AI is an educational course-project prototype. It is not a medical device, diagnostic system, prescribing system, or validated drug-interaction checker.

## Safety objective

The system is designed to **fail closed**: if the input, model output, or evidence cannot be validated, it should publish less information rather than inventing a confident conclusion.

## Guardrail layers

### 1. Input validation

- Lab Decoder accepts diagnostic reports, not product labels.
- Quick Ingredient/Product workflows accept product formulations, not clinical reports.
- Food and Skincare Cross-Match validate the inferred product type before interpretation.
- Written radiology findings/impressions are supported; raw DICOM interpretation is not.

### 2. Profile consistency

If the report explicitly prints an age or gender that contradicts the entered profile, personalized analysis is blocked. Missing demographics do not cause failure; the UI instead discloses that the profile could not be cross-verified.

### 3. OCR confidence

Empty/insufficient diagnostic findings or ingredient extraction cannot receive a normal concern verdict.

### 4. Structured-output validation

Agent responses must parse into the required Pydantic structures. One automatic repair attempt is allowed after malformed JSON. A second failure becomes **Unable to assess safely**.

### 5. Evidence guard

Numeric thresholds are retained only when the same number exists in retrieved evidence and the source is permitted by the high-stakes evidence registry. Absolute restrictions from non-verified bundled sources are downgraded.

### 6. Diagnosis guard

Prompts and post-processing distinguish findings from diagnoses. For example, a single severely reduced eGFR result is not automatically described as established chronic CKD when chronicity is not documented.

### 7. Exposure-route guard

Dietary/oral restrictions are not automatically transferred to topical skincare exposure. Route-inappropriate claims are down-ranked unless supplied evidence supports clinically meaningful systemic absorption.

### 8. Product-label claim guard

Observed quantities are retained only when the same number is visible in the extracted label text/facts.

### 9. eGFR guard

The deterministic adult CKD-EPI calculation is not added for age under 18, pregnancy, or clearly incompatible creatinine units. Reported eGFR and calculated eGFR remain separately labeled.

### 10. Interaction concern vs report severity

Cross-Match separates **product–report interaction concern** from **underlying report attention**. A low-interaction product cannot make a severely abnormal report appear low-risk overall.

## Known limitations

- The bundled knowledge base is deliberately small and includes some illustrative entries.
- Medication names provide context; the app is not a comprehensive interaction database.
- Search results may be incomplete or noisy.
- Heuristic concern scores are not probabilities of harm.
- No software architecture can guarantee zero medical error from an LLM; safe abstention and human review remain necessary.
