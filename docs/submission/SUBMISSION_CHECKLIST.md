# ExtraCare AI — Final Submission Checklist

The repository is structured to satisfy the supplied project brief. Items that require the student's own cloud accounts, API keys, browser, GitHub, YouTube, or LangSmith sharing intentionally remain unchecked until they are actually completed.

## Repository and security

- [x] Real-world problem, target users, and AI value are documented.
- [x] Working Streamlit frontend and structured backend are implemented.
- [x] Agents, OCR, RAG, Chroma vector DB, search grounding, and LangSmith instrumentation exist in the connected workflows.
- [x] `.env` and Streamlit secrets are ignored.
- [x] `.env.example` contains placeholders only.
- [x] README, dependency files, setup/run scripts, demo guide, rubric map, and validation scripts are present.
- [ ] Run `python scripts/preflight.py --submission` successfully on the actual submission machine.
- [ ] Add 3–5 screenshots from the actual running app to the GitHub repository if desired/appropriate.

## Live workflow proof

- [ ] Configure a valid `GROQ_API_KEY` and verify Groq OCR/chat.
- [ ] Configure a valid `TAVILY_API_KEY` and demonstrate Thorough-mode live search grounding.
- [ ] Configure `LANGSMITH_API_KEY` and set `LANGSMITH_TRACING=true`.
- [ ] Run `python scripts/validate_live.py` using only bundled synthetic sample data.
- [ ] Manually compare OCR/extracted values with the visible synthetic sample images.
- [ ] Open the nested LangSmith runs and confirm Router/agent/tool/retrieval/LLM/risk/final-output steps are visible as applicable.

## LangSmith submission links

- [ ] Run `python scripts/export_langsmith_traces.py` and inspect the three candidate root traces.
- [ ] After confirming synthetic-only content, run `python scripts/export_langsmith_traces.py --share --update-submission-links`.
- [ ] Lab Decoder trace link opens for the evaluator.
- [ ] Product Sentinel trace shows live search and opens for the evaluator.
- [ ] Cross-Match trace opens for the evaluator.

## English video

- [ ] Part 1 explains the real problem and target user.
- [ ] Part 1 demonstrates realistic working application flows and useful outputs.
- [ ] Part 1 visibly demonstrates OCR, retrieval/search, and agent/tool execution where appropriate.
- [ ] Part 2 explains architecture, folder structure, frontend/backend, LLM configuration, prompts, agents, tools, OCR, RAG, embeddings, Chroma, LangSmith, important functions, and environment setup.
- [ ] The student explains the implementation in their own words rather than only scrolling through code.

## Final links

- [ ] Complete GitHub repository URL added to `SUBMISSION_LINKS.md`.
- [ ] English YouTube presentation URL added to `SUBMISSION_LINKS.md`.
- [ ] LangSmith trace URLs added to `SUBMISSION_LINKS.md`.
- [ ] Every submitted URL was opened and verified before submission.
