# ExtraCare AI

**Personalized Health Intelligence & Safety Assistant**

ExtraCare AI is a real-world, multi-agent healthcare decision-support course-project prototype. It combines a user's health profile with diagnostic reports, product labels, retrieved evidence, and current external information to produce structured, traceable educational guidance.

> **Important:** ExtraCare AI is not a medical device and does not diagnose, prescribe, or replace licensed clinical care.

---

## 1. Problem & Target Users

### The problem
Health information is often fragmented. A person may receive a lab report, read a food or skincare label, search several sources, and still struggle to understand how those pieces relate to the same health context.

### Target users
Adults who want help organizing and understanding the relationship between:

- their health profile,
- written diagnostic reports,
- food / supplement / skincare labels,
- previous results in the current session,
- and evidence retrieved from the project knowledge base or live search.

### Why AI is useful
ExtraCare AI combines OCR/document extraction, retrieval, search, structured reasoning, specialized agents, and deterministic safety checks in one connected workflow instead of acting like a general-purpose chatbot.

---

## 2. Main User Workflows

ExtraCare AI currently provides seven connected modes:

1. **Lab Decoder** — analyzes blood panels, urinalysis/UACR, and written radiology reports.
2. **Product Sentinel** — reviews food, supplement/medicine ingredient labels, and skincare/cosmetic labels.
3. **Food Cross-Match** — combines a diagnostic report with a food label.
4. **Skincare Cross-Match** — combines a diagnostic report with a skincare/cosmetic label.
5. **Quick Ingredient Check** — fast typed-input or label-based ingredient checking.
6. **Disease Care & Protocol Hub** — general evidence-grounded disease education.
7. **My Health Timeline** — session-only activity history and change tracking.

All modes reuse the same Core Health Profile so the system behaves as one connected application rather than seven disconnected mini-tools.

---

## 3. Application Preview

> Add 3–5 clean screenshots here after saving them under `docs/screenshots/`.

| Home | Lab Decoder |
|---|---|
| `docs/screenshots/home.png` | `docs/screenshots/lab_decoder.png` |

| Product Sentinel | Cross-Match |
|---|---|
| `docs/screenshots/product_sentinel.png` | `docs/screenshots/cross_match.png` |

---

## 4. High-Level Architecture

```text
User
  ↓
Streamlit Frontend
  ↓
Core Health Profile
  ↓
Router / Workflow
  ↓
Specialized Agent
  ├── OCR / PDF Extraction
  ├── RAG Retrieval
  ├── Chroma Vector Store
  ├── Tavily Search
  └── Groq LLM
  ↓
Confidence + Safety / Risk Checks
  ↓
Final Structured Result
  ↓
LangSmith Trace
```

### Main execution patterns

```text
User Input
  → Router
  → Agent
  → Tool / Search / RAG
  → Processing
  → Final Response
```

```text
User Upload
  → OCR / Text Extraction
  → Information Extraction
  → Retrieval / Search
  → AI Analysis
  → Structured Result
```

---

## 5. AI, Agents & Tools

### LLM provider
This build uses **GroqCloud** for chat and vision/OCR workloads.

- Chat / reasoning model: `qwen/qwen3.6-27b`
- Vision / OCR model: `qwen/qwen3.6-27b`

### Specialized agents
The backend contains separate agent responsibilities such as:

- Router Agent
- Lab Agent
- Product Agent
- Cross-Match Agent
- Disease Hub Agent
- Arbiter / final-result logic

Agents are used only where they have a clear responsibility.

### Tooling
The system integrates:

- Groq LLM and vision/OCR
- Tavily live search
- RAG retrieval
- Chroma vector storage
- Local embeddings
- LangSmith tracing

---

## 6. OCR & Document Handling

Uploaded images and scanned documents can be processed through OCR/vision.

For machine-readable PDFs, the application prefers local text/table extraction when possible. This reduces unnecessary vision calls and makes document processing more reliable.

Example supported inputs include:

- blood reports,
- urinalysis/UACR reports,
- written radiology reports,
- food labels,
- supplement / medicine ingredient labels,
- skincare labels.

---

## 7. RAG & Vector Database

ExtraCare AI includes retrieval-based functionality.

### Knowledge sources
The bundled knowledge base is stored under:

```text
data/knowledge_base/
```

### Vector storage
The project uses **Chroma** for semantic retrieval.

### Retrieval flow

```text
Knowledge documents
  → chunking / prepared records
  → local embeddings
  → Chroma vector store
  → semantic retrieval
  → retrieved evidence
  → agent / LLM context
```

The system does not treat missing knowledge-base evidence as proof that something is safe.

---

## 8. Internet Search & Grounding

When current or external information is needed, ExtraCare AI can use **Tavily** search.

The intended flow is:

```text
User request
  → search decision
  → Tavily retrieval
  → grounded context
  → agent synthesis
  → final result
```

Search usage is kept traceable through the analysis workflow.

---

## 9. Safety & Confidence

ExtraCare AI applies deterministic safety and confidence checks around AI output.

Examples include:

- input validation,
- confidence gating,
- profile-aware restrictions,
- risk scoring,
- safe fallback behavior when analysis fails,
- conservative handling when evidence is insufficient.

The project is designed to fail closed rather than publish an unreliable clinical-style conclusion.

---

## 10. LangSmith Tracing

Important executions are instrumented with LangSmith tracing.

Representative traces should demonstrate:

1. **Lab Decoder**  
   `Router → OCR/Extraction → RAG → Lab Agent → Confidence → Risk → Arbiter`

2. **Product Sentinel**  
   `Router → OCR → RAG + Tavily → Product Agent → Confidence → Risk → Arbiter`

3. **Cross-Match**  
   `Parallel extraction → retrieval → Cross-Match Agent → Risk → Arbiter`

For final submission, share only synthetic/demo traces and place the links in:

```text
SUBMISSION_LINKS.md
```

---

## 11. Tech Stack

| Area | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| Agent / workflow orchestration | LangGraph / project workflow layer |
| LLM | GroqCloud |
| Chat / Vision model | Qwen 3.6 27B |
| OCR | Groq vision + local PDF/text extraction |
| Search | Tavily |
| RAG | Project retrieval pipeline |
| Vector DB | Chroma |
| Embeddings | Local embedding model |
| Tracing | LangSmith |
| Testing | Pytest |

---

## 12. Project Structure

```text
ExtraCare-AI/
├── backend/
│   ├── agents/
│   ├── config/
│   ├── controllers/
│   ├── core/
│   ├── models/
│   ├── rag/
│   ├── tools/
│   └── workflow/
│
├── frontend/
│   ├── app.py
│   ├── assets/
│   └── pages/
│
├── data/
│   ├── knowledge_base/
│   └── sample_images/
│
├── docs/
│   ├── screenshots/
│   └── ...
│
├── scripts/
├── tests/
├── .streamlit/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml
└── SUBMISSION_LINKS.md
```

---

## 13. Setup

### Requirements

- Python 3.11+ recommended
- Git
- Groq API key
- Tavily API key
- LangSmith API key

### Clone

```bash
git clone https://github.com/Sumaiya-Emu/ExtraCare-AI.git
cd ExtraCare-AI
```

### Setup

```powershell
py scripts/project.py setup
```

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Then add your own private keys to `.env`.

> Never commit `.env` or real API keys.

---

## 14. Environment Variables

Example:

```dotenv
GROQ_API_KEY=""
TAVILY_API_KEY=""

LANGSMITH_API_KEY=""
LANGSMITH_TRACING=true
LANGSMITH_PROJECT="ExtraCare-AI"

CHAT_MODEL_NAME="qwen/qwen3.6-27b"
VISION_MODEL_NAME="qwen/qwen3.6-27b"

EMBEDDING_MODEL_NAME="all-MiniLM-L6-v2"

GROQ_TIMEOUT_SECONDS=60
MAX_PDF_PAGES=3
DEFAULT_ANALYSIS_MODE=fast
```

---

## 15. Run

Validate the project:

```powershell
py scripts/project.py check
```

Run live integration checks:

```powershell
py scripts/project.py live
```

Start the application:

```powershell
py scripts/project.py run
```

Then open:

```text
http://localhost:8501
```

---

## 16. Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

---

## 17. Final Submission Links

Final links are maintained in:

```text
SUBMISSION_LINKS.md
```

They should include:

- GitHub repository
- English YouTube presentation
- representative LangSmith trace links

---

## 18. Academic / Safety Note

This repository is an educational course-project prototype. The bundled demo content should use synthetic test data only. Do not use the application as a replacement for professional medical advice, diagnosis, treatment, or emergency care.
