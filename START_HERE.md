# ExtraCare AI — complete project package

This ZIP contains the complete source, seven feature modules, sample images, curated knowledge base, dependency files, setup/run commands, tests, audit evidence, English presentation guide and submission checklist.

**Package status:** provider migration and static validation completed. Your API credentials, dependency installation, live validation, browser review and actual submission URLs are still required. Do not describe the Groq build as fully live-validated until those steps are complete.

## Windows — easiest setup

1. Install Python 3.11, 3.12, or 3.13 (Python 3.12 recommended) and enable **Add Python to PATH**.
2. Extract the ZIP completely. Open the `ExtraCare-AI` folder; do not run from inside the ZIP viewer.
3. Double-click `SETUP.bat`. It creates `.venv`, installs dependencies, copies `.env.example` to `.env` only when `.env` does not exist, and runs offline checks.
4. Open `.env` in a text editor and add your own credentials as shown below.
5. Double-click `RUN.bat`. Keep its terminal window open while using the app. Streamlit prints the local browser URL.
6. Use `CHECK.bat` whenever you want to rerun offline checks. Press Ctrl+C in the running terminal to stop the app.

Terminal equivalents, from the extracted project folder:

```powershell
py scripts/project.py setup
py scripts/project.py run
py scripts/project.py check
```

If `py` is unavailable, use `python` instead. On computers with several Python versions, use `py -3.12` for setup.

## macOS / Linux

From the extracted project folder:

```bash
bash project.sh setup
bash project.sh run
bash project.sh check
```

Some Linux distributions package Python's venv support separately. If setup reports that `venv` or `ensurepip` is missing, install the matching Python venv package through your system package manager, then retry.

## Configure live features

Edit the `.env` created by setup. Use your own values; never include this file in GitHub or your submission ZIP.

```dotenv
GROQ_API_KEY="your-own-key"
TAVILY_API_KEY="your-own-key"
LANGSMITH_API_KEY="your-own-key"
LANGSMITH_TRACING=true
LANGSMITH_PROJECT="ExtraCare-AI"
```

The text above is illustrative, not working credentials. Leave the model settings from `.env.example` unchanged unless your provider account requires a different supported model. Restart the app after changing `.env`.

| Setting | Needed for |
|---|---|
| Groq API key | Multimodal OCR and cloud LLM analysis |
| Tavily API key | Internet-search grounding in supported Thorough-mode workflows |
| LangSmith key and tracing enabled | Recording the required execution traces |

Without Groq credentials, covered deterministic typed checks and local Disease Hub guidance can still run. That limited path does not demonstrate the brief's mandatory OCR, semantic RAG, live search and tracing together.

## Reproduce the verified local outputs

On Windows:

```powershell
.venv\Scripts\python scripts/verify_offline_outputs.py
```

On macOS/Linux:

```bash
.venv/bin/python scripts/verify_offline_outputs.py
```

Inspect `docs/audit_evidence/offline_outputs.json` and `sample_doctor_brief.md`. These are real local function outputs, not live OCR/LLM results.

## Run the live checks before recording

After setting the keys and enabling tracing:

```powershell
py scripts/project.py live
```

On macOS/Linux use `bash project.sh live`.

This makes real provider requests using bundled synthetic samples and may consume API credits. It records structured outputs in `docs/audit_evidence/live_results.json`. Manually compare every extracted value and ingredient against the original image. Open LangSmith and verify the actual runs and tool transitions; a script success message alone does not verify evaluator access to a trace.

Then locate the three required root traces without changing their sharing status:

```powershell
.venv\Scripts\python scripts/export_langsmith_traces.py
```

After checking that the selected traces contain **synthetic data only**, explicitly create public share links and write them into `SUBMISSION_LINKS.md`:

```powershell
.venv\Scripts\python scripts/export_langsmith_traces.py --share --update-submission-links
```

Open every generated link in an incognito/private browser before submission.

## Suggested presentation sequence

1. Home page: problem, target users and shared health profile.
2. Lab Decoder: sample blood panel with a **synthetic sidebar profile** (for example age 55, Female). The sample report itself does not print age/gender; do not claim OCR extracted those demographics. Show structured OCR, findings, underlying report attention and Doctor Visit Brief.
3. Follow-up sample: show CareDelta with the same profile.
4. Product Sentinel in **Thorough** mode: show label OCR, retrieved evidence, actual search status and LangSmith trace.
5. Food Cross-Match: demonstrate report plus product and explain the two concern summaries.
6. Disease Hub: distinguish general condition education from personalized analysis.
7. Code walkthrough: follow `docs/DEMO_SCRIPT.md` and explain the tests and limitations.

Use synthetic samples for public demonstrations. A local heuristic concern score is not a clinical diagnosis or probability of harm.

## Files to read before submitting

| File | Purpose |
|---|---|
| `README.md` | Architecture, features, settings and implementation explanation |
| `AUDIT_REPORT.md` | Defects fixed, test evidence, limitations and requirement mapping |
| `SUBMISSION_CHECKLIST.md` | Final completion checklist |
| `SUBMISSION_LINKS.md` | Place your actual GitHub, English YouTube and LangSmith URLs |
| `docs/DEMO_SCRIPT.md` | English demonstration and code walkthrough outline |
| `docs/PROJECT_REQUIREMENTS.md` | The supplied project brief |
| `docs/LIVE_VALIDATION.md` | Live output and workflow checks |
| `docs/audit_evidence/` | Saved test and local output evidence |

## Final submission actions

- Publish the complete source to your own GitHub repository, excluding `.env`, `.venv`, generated vector stores and personal health data.
- Capture actual browser screenshots after checking layout and outputs.
- Record and upload the English demonstration and code explanation.
- Capture evaluator-accessible LangSmith traces for lab, product/search and cross-match.
- Add the real URLs to `SUBMISSION_LINKS.md` and check that each opens correctly.

These account-specific deliverables are not created by extracting this ZIP. No working API keys, fabricated screenshots, invented URLs or fake cloud traces are included.
