# Live Validation Checklist

Run this checklist on the submitter's machine after adding real API keys. These checks cannot be completed by static source inspection alone.

## Environment

1. Create `.env` from `.env.example`.
2. Add a valid `GROQ_API_KEY`.
3. Add `TAVILY_API_KEY` for live-search demonstration.
4. Add `LANGSMITH_API_KEY` and set `LANGSMITH_TRACING=true` for submission traces. Legacy `LANGCHAIN_*` aliases also work.
5. Run `python scripts/run_submission_checks.py`, then `python scripts/validate_live.py`.
   The latter makes real provider calls with synthetic sample inputs and records outputs; missing keys produce NOT RUN.
6. Run `python -m streamlit run frontend/app.py`.

## Live workflow checks

### Lab Decoder

- Upload a blood panel and verify extracted values against the original document.
- Upload a qualitative urinalysis and confirm values such as Trace/2+/Few remain textual.
- Upload a written radiology report and confirm the app extracts text rather than interpreting raw imaging.
- Change the profile after analysis and verify the old personalized result is hidden.

### Product Sentinel

- Verify product type, exposure route, ingredients, and visible quantities.
- In Fast mode, confirm live Tavily search is skipped.
- In Thorough mode with a valid Tavily key, confirm a search call is visible in LangSmith.

### Cross-Match

- Put a skincare label into Food Cross-Match and verify the type gate blocks the result.
- Put a food label into Skincare Cross-Match and verify the reciprocal gate.
- Confirm the UI shows interaction concern separately from underlying report attention.

### Disease Care Hub

- Fast mode should provide conservative local evidence when available.
- Thorough mode should use RAG/live grounding when configured.
- If live generation fails, the UI should fall back instead of crashing.

### Timeline

- Analyze two lab reports with the same profile and verify CareDelta.
- Clear session health memory and verify counters immediately reset.

## LangSmith traces to submit

Capture at least:

1. Lab Decoder — router → OCR → RAG → specialist → confidence → deterministic risk → dossier.
2. Product Sentinel Thorough — OCR → toxicology RAG + Tavily → specialist → risk → dossier.
3. Cross-Match — parallel OCR → parallel retrieval → cross-match specialist → risk → dossier.

Do not include API keys or unnecessary sensitive content in screenshots or repository files.

## Export evaluator-accessible trace links

After the live synthetic validation succeeds, first inspect recent candidates without making anything public:

```bash
python scripts/export_langsmith_traces.py
```

After confirming the three selected traces contain only the bundled synthetic demo data, create share links intentionally:

```bash
python scripts/export_langsmith_traces.py --share --update-submission-links
```

The script writes `docs/audit_evidence/langsmith_trace_links.json` and can update the LangSmith rows in `SUBMISSION_LINKS.md`. Open each public link in a private/incognito window before submission.
