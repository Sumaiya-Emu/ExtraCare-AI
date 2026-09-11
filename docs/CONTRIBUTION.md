# ExtraCare AI — Student Contribution Map

This document is intentionally included to make the student's design ownership easy to explain during evaluation.

## Product/problem contribution

The project is framed around one question: **how does the same lab result, ingredient, or product change meaning when the user's health context changes?** The student-defined product concept is therefore a shared Core Health Profile feeding multiple decision workflows rather than seven disconnected chatbots.

## Student-designed features

- **Graduated restriction model:** separates complete avoidance from quantity/dose/context-dependent caution.
- **CareGraph:** visual relationship view connecting health context, findings, and ingredient restrictions.
- **CareDelta:** session-based comparison of repeated laboratory results without claiming that every increase/decrease is good or bad.
- **CareSwap:** actionable selection criteria rather than unsupported brand recommendations.
- **Confidence Gate:** blocks a verdict when extraction/model validation is insufficient.
- **Doctor Visit Brief:** turns the already-validated structured output into questions and a clinician handoff without another diagnostic model call.
- **Food vs Skincare Cross-Match:** validates product type and exposure route before applying report context.
- **Disease Care Hub:** separates general educational disease guidance from profile-specific report/product analysis.

## Clinical-safety contribution

The student can explain these explicit design rules:

1. Malformed AI output must never become an empty finding list and therefore a false safe result.
2. No verified evidence means no numeric threshold.
3. General warnings for conditions not in the user's profile are educational, not personalized danger flags.
4. A single abnormal result is not automatically a confirmed chronic diagnosis.
5. A topical ingredient is not treated as equivalent to oral ingestion without route-specific evidence.
6. A report/profile demographic contradiction blocks personalized interpretation.
7. Cross-Match shows underlying report attention separately from product-interaction concern.
8. Session history is private-by-default and not written to a persistent database.

## Technical contribution

The student should be prepared to explain:

- why Streamlit was chosen for rapid end-to-end demonstration;
- why frontend code calls backend controllers instead of LLM/RAG functions directly;
- why Chroma uses separate clinical and toxicology collections;
- why typed Pydantic contracts sit between OCR/agents/UI;
- how profile-aware retrieval queries are built;
- why Fast mode skips live search and the extra narrative synthesis call;
- where parallel OCR/RAG/search reduce latency;
- how LangSmith traces expose the workflow;
- why all UI styling is kept in `frontend/assets/style.css`.

## Manual evaluation contribution

The repository includes synthetic samples and regression tests. The student should run the demo cases, compare OCR extraction with the source report/label, inspect LangSmith traces, and document any limitation found before recording the final presentation.
