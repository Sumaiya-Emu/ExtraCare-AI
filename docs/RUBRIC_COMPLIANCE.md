# ExtraCare AI — Rubric Compliance Map

This file maps the supplied Final Project Submission Brief to concrete implementation evidence. It intentionally distinguishes **implemented in the repository** from **account-specific proof that must still be produced on the submitter's machine**.

| Brief requirement | Repository evidence | Final proof required |
|---|---|---|
| Real-world AI application | README problem/target-user section; shared health-context use case | Explain the problem and user in the English video |
| Usable front end | `frontend/app.py`, seven Streamlit feature pages, shared `ui_common.py` | Open the real app in a browser and demonstrate the main journey |
| Structured back end | `backend/controllers/`, `agents/`, `core/`, `rag/`, `tools/`, `workflow/` | Explain separation of concerns in the code walkthrough |
| Meaningful agents | Router, Lab, Product, Cross-Match, Text Check, Disease Hub, Arbiter | Show the relevant agent spans in LangSmith |
| External tools | Groq Qwen multimodal extraction, Tavily search, Chroma retrieval | Demonstrate at least one real tool call |
| Internet search / grounding | `backend/tools/search_tool.py`; Product Sentinel and Disease Hub Thorough mode | Valid Tavily key + Thorough-mode search execution |
| OCR | `backend/tools/ocr_tool.py`; image/PDF preprocessing in `pdf_utils.py` | Compare synthetic sample OCR output with the visible sample |
| RAG | `backend/rag/retriever.py`; profile-aware queries in `query_builder.py` | Show retrieved context/trace before generation |
| Vector database | Chroma in `backend/rag/vector_store.py`; local all-MiniLM-L6-v2 embeddings | Explain collections, record-level chunks, embeddings, retrieval |
| Complete connected workflow | LangGraph in `backend/workflow/graph.py` | Demonstrate input → router/agent → tools/RAG → risk → final result |
| LangSmith tracing | `backend/core/tracing.py`; traced agents/tools/retrievers/workflow | Real LangSmith project, nested traces, evaluator-accessible links |
| Code quality | Pydantic schemas, controllers, modular folders, external CSS, tests, fail-closed errors | Run preflight on the submission machine |
| Secret hygiene | `.gitignore`, placeholder-only `.env.example`, credential scan in preflight | Ensure `.env` is absent from GitHub and submitted ZIP |
| README/setup instructions | `README.md`, `START_HERE.md`, `SETUP.bat`, `RUN.bat`, `project.sh` | Verify clean setup/run on the actual demo machine |
| English YouTube presentation | `docs/DEMO_SCRIPT.md` | Record/upload the English video and verify its URL |
| GitHub repository | Complete source package is ready to publish | Push to the student's GitHub account and verify repository URL |
| LangSmith trace submission | `scripts/validate_live.py`, `scripts/export_langsmith_traces.py` | Run with real keys, inspect synthetic traces, share selected links |
| Academic integrity / explainability | `docs/CONTRIBUTION.md`, architecture docs/tests | Student explains architecture, functions, prompts, RAG, tools and decisions |

## What the vector store contains

The bundled clinical and toxicology JSON records are transformed into one semantic document per curated fact record. The repository does not claim arbitrary fixed-token chunking for these short structured entries. Each Chroma collection is namespaced by embedding model so incompatible embeddings are not mixed.

## Main trace shape to demonstrate

```text
User request / upload
        ↓
Router Agent
        ↓
Specialized Agent
        ↓
OCR Tool (when image/PDF input exists)
        ↓
Chroma RAG Retriever ─── Tavily Search (where applicable)
        ↓
LLM structured analysis
        ↓
Confidence Gate
        ↓
Deterministic Risk Engine
        ↓
Arbiter / Final Dossier
        ↓
Patient + Clinical views / Doctor Brief / CareGraph
```

The exact nested order differs by mode. Product analysis fans out RAG and live search after OCR; Cross-Match performs parallel OCR and parallel clinical/toxicology retrieval.

## Truthful completion rule

A repository checkbox is not equivalent to final submission proof. The code can implement OCR, RAG, search and tracing, but the final evaluator-facing requirements are complete only after valid credentials are configured, live synthetic workflows succeed, LangSmith retains the traces, the trace links are shared intentionally, the app is visually checked, and GitHub/YouTube URLs exist.
