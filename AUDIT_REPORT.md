# ExtraCare AI — Groq Migration Audit

## Scope

This audit records the migration of the submission package from Google AI Studio/Gemini to **GroqCloud** while preserving the course-required agent, OCR, RAG, vector-database, live-search, and LangSmith workflow.

## Implemented changes

- `GROQ_API_KEY` replaces `GOOGLE_API_KEY`.
- `backend/tools/groq_client.py` uses LangChain `ChatGroq`.
- Default chat/vision model: `qwen/qwen3.6-27b`.
- Groq JSON mode is requested and reasoning output is hidden by default so structured parsing is not polluted by `<think>` blocks.
- OCR uses Groq/OpenAI-compatible `image_url` base64 JPEG content blocks.
- PDF OCR is capped at three rendered pages per request and reports truncation when the source has more pages.
- Google embedding APIs were removed. Chroma's local `all-MiniLM-L6-v2` embedding function now powers semantic retrieval.
- Tavily search grounding and LangSmith tracing are unchanged.
- The secret scanner now checks common Groq `gsk_` credential patterns.

## Static validation completed

- Python compilation: PASS.
- Knowledge-base JSON parsing: PASS.
- No remaining runtime Gemini/Google-AI provider references: PASS.
- `.env` excluded and `.env.example` placeholder-only: PASS.

## Live validation still required

The package intentionally contains no real API credentials. The build environment also lacked outbound PyPI DNS during dependency installation, so no live Groq/Tavily/LangSmith execution is claimed here. On the final Windows machine run `py scripts/project.py setup`, configure `.env`, then run `py scripts/project.py check` and `py scripts/project.py live`. The live command exercises the bundled synthetic Lab, Product, and Cross-Match workflows and records root run IDs for LangSmith trace submission.

## Provider note

**Groq** is the inference/API provider used here. It is not **Grok**, the xAI model family.

- Dependency-light Groq migration regression tests: **6 passed** in the build sandbox.
