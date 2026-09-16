# Actual submission links

Replace PENDING only with links you have created and checked. These are submission requirements, not code-test results.

| Deliverable | Link / status |
|---|---|
| LangSmith Lab Decoder trace | https://smith.langchain.com/public/7645d971-211a-4911-b87c-3fa1c5f8e9b4/r |
| LangSmith Product Sentinel trace with live search | https://smith.langchain.com/public/13de5e7f-b95a-4ca5-bee6-31ae084383b7/r |
| LangSmith Cross-Match trace | https://smith.langchain.com/public/a368eb8b-dafc-48e4-a275-76614c0888db/r |

Run `python scripts/run_submission_checks.py`, then `python scripts/validate_live.py` with your own keys before recording. Inspect recent trace candidates with `python scripts/export_langsmith_traces.py`; only after confirming synthetic-only contents, use `--share --update-submission-links`. Manually verify extracted text and every public link. Share only synthetic test data in public demo materials.
