# ExtraCare AI

**Personalized Health Information & Safety Assistant**

ExtraCare AI is a health-focused AI application that helps users understand medical reports, product labels, ingredients, and general health information in one place.

The app uses one shared health profile across its different features. It can read uploaded documents, retrieve relevant information, search the web when needed, and use different AI agents to prepare the result.

> **Important:** ExtraCare AI is an educational project. It does not diagnose diseases, prescribe treatment, or replace professional medical care.

---

## 1. Problem & Target Users

### The Problem

Health information can be difficult to understand because it often comes from different sources.

For example, a user may have a medical report, a food or skincare label, and information from different websites. It can be difficult to understand how these things relate to the same health situation.

ExtraCare AI brings this information together and presents it in a simpler way.

### Target Users

The project is mainly designed for adults who want help understanding:

- their basic health profile
- diagnostic reports
- food, supplement, or skincare labels
- individual ingredients
- recent results from the current session
- information from the local knowledge base or web search

### Why I Used AI

Different types of information need different types of processing.

ExtraCare AI can read uploaded files, retrieve useful information, search external sources when needed, and use different agents for different tasks.

---

## 2. Main Features

ExtraCare AI has seven main features.

### Lab Decoder

Helps users understand blood reports, urinalysis/UACR reports, and written radiology reports.

### Product Sentinel

Checks food, supplement, medicine ingredient, and skincare labels using the user's health profile.

### Food Cross-Match

Checks a diagnostic report together with a food product.

### Skincare Cross-Match

Checks a diagnostic report together with a skincare or cosmetic product.

### Quick Ingredient Check

Allows the user to type an ingredient name or upload a label for a quick check.

### Disease Care & Protocol Hub

Provides general information about selected health conditions.

### My Health Timeline

Keeps recent activity and results during the current session.

All of these features use the same **Core Health Profile**.

---

## 3. Application Preview

### Home

![ExtraCare AI Home](docs/screenshots/home.png)

### Lab Decoder

![Lab Decoder](docs/screenshots/lab_decoder.png)

### Product Sentinel

![Product Sentinel](docs/screenshots/product_sentinel.png)

### Cross-Match

![Cross-Match](docs/screenshots/cross_match.png)

---

## 4. How the System Works

The general workflow is:

```text
User
  ↓
Streamlit Frontend
  ↓
Core Health Profile
  ↓
Router
  ↓
Selected Agent
  ↓
OCR / RAG / Search / Tools
  ↓
AI Analysis
  ↓
Confidence and Safety Checks
  ↓
Final Result
```

For uploaded files:

```text
File Upload
  ↓
OCR or Text Extraction
  ↓
Information Extraction
  ↓
Retrieval or Web Search
  ↓
Agent Analysis
  ↓
Final Result
```

LangSmith is used to trace important workflow steps.

---

## 5. Agents

Different agents are used for different tasks.

The main agents include:

- Router Agent
- Lab Agent
- Product Agent
- Cross-Match Agent
- Disease Hub Agent
- Arbiter / final result logic

The **Router Agent** selects the correct workflow.

The **Lab Agent** works with diagnostic reports.

The **Product Agent** works with product information.

The **Cross-Match Agent** checks two related inputs together.

Each agent has a specific role in the application.

---

## 6. LLM and Tools

### LLM Provider

The project uses **GroqCloud** for the main AI processing.

Current model settings:

```text
Chat model: qwen/qwen3.6-27b
Vision/OCR model: qwen/qwen3.6-27b
```

### Main Tools

The application uses:

- Groq for AI processing
- Tavily for web search
- OCR and PDF extraction
- RAG retrieval
- Chroma vector database
- local embeddings
- LangSmith tracing

---

## 7. OCR and Document Processing

ExtraCare AI can work with uploaded images, scanned documents, and machine-readable PDFs.

If a PDF already contains readable text, the application can extract the text directly.

For images or scanned documents, the OCR/vision workflow can read the visible information.

Example inputs include:

- blood reports
- urinalysis/UACR reports
- written radiology reports
- food labels
- supplement labels
- medicine ingredient labels
- skincare labels

---

## 8. RAG and Vector Database

The project uses **RAG** to retrieve useful information before the final AI analysis.

The local knowledge base is stored in:

```text
data/knowledge_base/
```

The basic retrieval flow is:

```text
Knowledge Base
  ↓
Embeddings
  ↓
Chroma Vector Store
  ↓
Relevant Information
  ↓
Agent Context
  ↓
Final Analysis
```

The project uses **Chroma** as the vector database.

The local embedding model converts text into numerical representations so that related information can be found even when the wording is different.

---

## 9. Web Search

ExtraCare AI can use **Tavily** when current or external information is needed.

The general search flow is:

```text
User Request
  ↓
Search Decision
  ↓
Tavily Search
  ↓
Search Results
  ↓
Agent Analysis
  ↓
Final Response
```

Web search is used only when the workflow needs external information.

---

## 10. Safety and Confidence

Because the project works with health-related information, several checks are used around the AI output.

These include:

- input validation
- confidence checks
- health-profile checks
- risk checks
- fallback responses
- handling incomplete information

If there is not enough reliable information, the application can stop the analysis instead of guessing.

The project is designed for educational support, not medical diagnosis or treatment.

---

## 11. LangSmith Tracing

LangSmith is used to inspect important workflows inside ExtraCare AI.

It allows me to see steps such as:

- routing
- agent execution
- OCR/tool calls
- retrieval
- web search
- model execution
- final processing

### Lab Decoder Trace

[Open Lab Decoder LangSmith Trace](https://smith.langchain.com/public/7645d971-211a-4911-b87c-3fa1c5f8e9b4/r)

### Product Sentinel Trace

[Open Product Sentinel LangSmith Trace](https://smith.langchain.com/public/13de5e7f-b95a-4ca5-bee6-31ae084383b7/r)

### Cross-Match Trace

[Open Cross-Match LangSmith Trace](https://smith.langchain.com/public/a368eb8b-dafc-48e4-a275-76614c0888db/r)

The same submission links are also available in:

```text
SUBMISSION_LINKS.md
```

---

## 12. Tech Stack

| Area | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| Workflow | LangGraph |
| LLM | GroqCloud |
| Chat / Vision Model | Qwen 3.6 27B |
| OCR | Groq Vision + local text extraction |
| Search | Tavily |
| RAG | Local retrieval pipeline |
| Vector Database | Chroma |
| Embeddings | all-MiniLM-L6-v2 |
| Tracing | LangSmith |
| Testing | Pytest |

---

## 13. Project Structure

```text
ExtraCare-AI/
│
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
│   └── screenshots/
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

## 14. Setup

### Requirements

- Python 3.11 or newer
- Git
- Groq API key
- Tavily API key
- LangSmith API key

### Clone the Repository

```bash
git clone https://github.com/Sumaiya-Emu/ExtraCare-AI.git
cd ExtraCare-AI
```

### Setup the Project

```powershell
py scripts/project.py setup
```

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Then add your own API keys to `.env`.

> Never upload the real `.env` file or API keys to GitHub.

---

## 15. Environment Variables

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

## 16. Run the Application

First, check the project:

```powershell
py scripts/project.py check
```

Then start the application:

```powershell
py scripts/project.py run
```

The application should open at:

```text
http://localhost:8501
```

If needed, Streamlit can also be started directly:

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend\app.py
```

---

## 17. Tests

Run the tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The project includes tests for important application and workflow behavior.

---

## 18. Submission Links

The final submission links are available in:

```text
SUBMISSION_LINKS.md
```

They include:

- GitHub repository
- English YouTube presentation
- Lab Decoder LangSmith trace
- Product Sentinel LangSmith trace
- Cross-Match LangSmith trace

---

## 19. Safety Note

ExtraCare AI was created as an educational course project.

The demonstration uses sample or synthetic data.

The application is not intended to replace professional medical advice, diagnosis, treatment, or emergency care.