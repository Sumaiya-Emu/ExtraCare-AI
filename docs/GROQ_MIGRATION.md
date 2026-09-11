# Groq Migration

ExtraCare AI now uses **GroqCloud**, not Google AI Studio, for chat and multimodal OCR.

- Provider: GroqCloud
- Default chat/vision model: `qwen/qwen3.6-27b`
- Secret: `GROQ_API_KEY` in the ignored `.env` only
- OCR: base64 JPEG pages sent through the Groq-compatible vision message format
- RAG embeddings: Chroma's local `all-MiniLM-L6-v2` default embedding function
- Vector database: persistent Chroma
- Internet grounding: Tavily
- Tracing: LangSmith

The local embedding model may download its model files on first use. It does not require a Google or Hugging Face API key. The default PDF OCR limit is three pages per model request to match the configured Qwen vision model's current input-image limit.

For live validation use your own credentials:

```powershell
py scripts/project.py setup
# edit .env, then:
py scripts/project.py check
py scripts/project.py live
py scripts/project.py run
```
