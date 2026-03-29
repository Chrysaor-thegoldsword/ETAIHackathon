# ET Money Mentor

ET Money Mentor is a hackathon-ready AI financial advisor prototype for the Economic Times ecosystem. It runs a guided client interview, optionally ingests uploaded finance documents, calculates a financial wellbeing score, compares tax regimes for FY 2025-26, recommends a goal-linked portfolio, and produces a downloadable PDF report.

## What it does

- ET-inspired front end with a premium newsroom/wealth aesthetic
- Guided advisor chat that collects profile, income, expenses, assets, liabilities, tax choices, and goals
- Optional upload flow for ITR, Form 16, and statement PDFs
- Financial health score out of 100 with red flags and core metrics
- Goal planning with monthly investment targets and milestones
- Tax comparison between old and new regimes using FY 2025-26 assumptions
- Portfolio split across equity, debt, gold, and cash
- Source-backed watchlist with official and broker research links
- PDF report generation for the final advisory summary

## Stack

- FastAPI
- Vanilla HTML/CSS/JavaScript
- ReportLab for PDF generation
- PyPDF for lightweight PDF text extraction

## Run locally

This project requires a `GROQ_API_KEY` for the chatbot to work properly.

```bash
python -m pip install -r requirements.txt
uvicorn src.main:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Groq API key setup

You need a Groq API key to run the LLM-powered advisor locally.

Steps to get the key:

1. Go to the [Groq Console](https://console.groq.com/).
2. Sign in or create a Groq account.
3. Open the [API Keys page](https://console.groq.com/keys).
4. Create a new API key.
5. Copy the key and keep it private.

Recommended setup:

1. Copy `.env.example` to `.env`.
2. Add your Groq key to `.env`.
3. Optionally keep the default model or change it.

Example:

```env
GROQ_API_KEY=your_real_groq_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

Official Groq references:

- [Groq Quickstart](https://console.groq.com/docs/quickstart)
- [Groq OpenAI Compatibility](https://console.groq.com/docs/openai)

## Run with the BAT file

If you are on Windows, you can also start the app by double-clicking `run_et_money_mentor.bat`.

What it does:

- switches to the project folder automatically
- reads `GROQ_API_KEY` and `GROQ_MODEL` from `.env` if available
- prompts for the Groq API key if it is missing
- installs the required Python packages
- starts the app on `http://127.0.0.1:8000`

You can also run it from PowerShell:

```powershell
.\run_et_money_mentor.bat
```

## Main files

- `SYSTEM_ARCHITECTURE.md` - Mermaid system architecture diagram
- `SYSTEM_ARCHITECTURE.png` - PNG export of the system architecture diagram
- `src/main.py` - FastAPI app and API routes
- `src/agents/conversation.py` - guided advisor flow
- `src/agents/health_score.py` - score engine and red flags
- `src/agents/goal_planner.py` - milestone and SIP planning
- `src/agents/tax_optimizer.py` - old vs new regime comparison
- `src/agents/portfolio_recommender.py` - allocation and watchlist logic
- `src/agents/report_generator.py` - structured report and PDF export
- `src/frontend/index.html` - UI shell
- `src/frontend/styles.css` - ET-style presentation layer
- `src/frontend/app.js` - chat, upload, dashboard rendering

## Notes

- This is an educational hackathon prototype.
- Tax assumptions are aligned to FY 2025-26 / AY 2026-27 logic used in the current build.
- Market recommendations are source-backed demo suggestions and should be connected to a live knowledge store for production use.
