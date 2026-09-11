# English Presentation Demo Script

## Part 1 — User demonstration

### Opening

"ExtraCare AI is a personalized health intelligence and safety assistant. Instead of explaining a lab value or ingredient in isolation, it connects one health profile with diagnostic reports, product labels, evidence, and previous results. It is an educational decision-support prototype, not a medical device."

### Demo A — Lab Decoder

1. For the bundled blood panel, set a synthetic sidebar profile such as age 55 and Female. State clearly that the sample report does **not** print age/gender; those values come from the Core Health Profile.
2. Upload the synthetic blood panel.
3. Show OCR extraction and the input completeness gate.
4. Show underlying report attention, key findings, specialist routing, and Clinical View evidence.
5. Analyze the follow-up report and open CareDelta.
6. Open the Doctor Visit Brief.

### Demo B — Product Sentinel

1. Use a condition/profile relevant to the sample label.
2. Show visible ingredients and quantities extracted by OCR.
3. Explain fully restricted vs dose/context-dependent restrictions.
4. Show CareSwap and evidence provenance.
5. Switch to Thorough mode and show the Tavily/LangSmith trace if configured.

### Demo C — Cross-Match

1. Upload one diagnostic report and one food label.
2. Explain that the system validates the product type first.
3. Show the product–report interaction concern and the separate underlying report attention.
4. Open CareGraph.

### Demo D — Disease Care Hub

Show that this page is general educational guidance and is intentionally separated from personalized report/product analysis.

## Part 2 — Code/architecture walkthrough

Explain in this order:

1. `frontend/` renders UI and calls controllers only.
2. `backend/controllers/` is the frontend/backend boundary.
3. `backend/workflow/graph.py` orchestrates Router → Specialist → Confidence → Risk → Dossier.
4. `backend/tools/groq_client.py` configures the Groq Qwen model; `backend/tools/ocr_tool.py` performs structured multimodal extraction.
5. `backend/rag/` implements Chroma + local all-MiniLM-L6-v2 embeddings + profile-aware retrieval.
6. `backend/core/safety/` contains deterministic guardrails.
7. `backend/core/risk_engine.py` is deterministic and the score is explicitly heuristic.
8. `backend/core/tracing.py` adds privacy-aware custom spans, tool/retriever labels, and context-preserving parallel workers so important executions are easy to inspect in LangSmith.
9. `tests/` contains core, audit-regression and offline workflow cases.
10. `docs/CONTRIBUTION.md` explains the student's own design contribution.

## LangSmith trace walkthrough during the video

For at least one trace, expand the nested run tree and explain: user mode/profile context → Router → OCR tool → RAG retriever → specialized agent → optional search tool → Confidence Gate → deterministic Risk Engine → Arbiter/final response. Show the LLM calls nested under the relevant agent/tool spans. Use only synthetic demo inputs in a publicly shared trace.
