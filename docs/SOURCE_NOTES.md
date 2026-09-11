# Source notes for the bundled demo knowledge base

The bundled JSON data is intentionally small and must not be treated as a comprehensive clinical
knowledge source.

Two explicit checks added during the ExtraCare AI upgrade:

- **UACR albuminuria categories:** KDIGO 2024 CKD material uses A1 <30 mg/g, A2 30–300 mg/g,
  A3 >300 mg/g.
- **Pregnancy caffeine context:** ACOG patient/clinical guidance describes moderate caffeine intake
  as less than 200 mg/day.

Other JSON entries retain their own source/disclaimer text. Some are marked “general clinical
reference” or “not independently re-verified”; that wording is intentional and should not be removed
for presentation polish.

For any production-like extension, replace summary records with versioned primary guideline excerpts
or an appropriately licensed/maintained medical knowledge source and record retrieval provenance.
