# Dependency and Model Configuration

Updated for the Groq migration on **2026-09-10**.

`requirements.txt` is the installation source used by `scripts/project.py setup`. `requirements.lock` is an advisory frozen reference and is not used by the setup command; platform-specific transitive packages can differ.

## Direct runtime dependencies

- Streamlit `1.63.0`
- Pydantic `2.13.5`
- PyMuPDF `1.28.2`
- Pillow `12.3.0`
- LangGraph `1.2.11`
- LangChain Core `1.6.2`
- `langchain-groq` `1.1.3`
- `langchain-chroma` `1.1.0`
- ChromaDB `1.5.9`
- LangSmith `0.12.1`
- Tavily Python `0.8.1`

## Model choices

- Chat / multimodal OCR: `qwen/qwen3.6-27b` through GroqCloud
- Semantic embeddings: Chroma local `all-MiniLM-L6-v2`
- Groq reasoning output: `hidden`
- Default Qwen reasoning effort: `none` (set `GROQ_REASONING_EFFORT=default` to enable reasoning)
- Default PDF OCR pages per request: `3`

The Qwen model is currently a Groq preview model, so hosted-model availability should be checked immediately before the recorded demo. `scripts/validate_live.py` performs a real end-to-end check with the submitter's own credentials. The local Chroma embedding model may download its model files automatically on first use; it does not require a Google or Hugging Face API key.

The build environment used for this migration could not reach PyPI, so a fresh post-migration `pip check` was not fabricated. Run `py scripts/project.py setup` and `py scripts/project.py check` on the final machine.
