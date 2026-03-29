# ET Money Mentor System Architecture

This diagram reflects the current implementation in this repository.

```mermaid
flowchart TB
    U["End User"] --> FE["ET-style Frontend\nindex.html + ui-v2.js + ui-v2.css"]

    FE -->|Chat message| API["FastAPI Backend\nsrc/main.py"]
    FE -->|PDF / ITR / Form 16 upload| API
    FE -->|Download report| API

    API --> CHAT["Conversation Session Manager\nConversationSession"]
    API --> UPLOAD["Document Upload Handler\n/api/upload"]
    API --> REPORT["Report Endpoint\n/api/report"]
    API --> STORE["In-memory Session Store\nsessions dict"]

    CHAT --> PROFILE["Profile Builder\nUserProfile"]
    CHAT --> LLM["LLM Layer\nsrc/agents/llm.py"]
    LLM --> GROQ["Groq API\nOpenAI-compatible endpoint"]

    UPLOAD --> DOC["Document Extraction\nsrc/agents/doc_extraction.py"]
    DOC --> PROFILE

    CHAT --> HEALTH["Health Score Engine\nhealth_score.py"]
    CHAT --> GOALS["Goal Planner\ngoal_planner.py"]
    CHAT --> TAX["Tax Optimizer\ntax_optimizer.py"]
    CHAT --> PORT["Portfolio Recommender\nportfolio_recommender.py"]

    PROFILE --> GOALS
    PROFILE --> TAX
    PROFILE --> HEALTH
    PROFILE --> PORT

    GOALS --> ANALYSIS["Unified Financial Analysis"]
    TAX --> ANALYSIS
    HEALTH --> ANALYSIS
    PORT --> ANALYSIS

    ANALYSIS --> REPGEN["Report Generator\nreport_generator.py"]
    REPORT --> REPGEN
    REPGEN --> PDF["PDF Builder\nReportLab output"]
    PDF --> FE

    PORT --> SOURCES["Source-backed recommendation links\nbroker / official references"]
```

## Component notes

- **Frontend** captures profile answers, uploads documents, renders progress, shows the financial dashboard, and downloads the report.
- **FastAPI backend** exposes the three main endpoints: `/api/chat`, `/api/upload`, and `/api/report`.
- **Conversation session manager** orchestrates onboarding, stores progress in memory, and decides when to trigger analysis.
- **LLM layer** handles conversational understanding, field extraction, reprompts, in-scope answers, and final summary generation using Groq.
- **Document extraction** parses uploaded PDFs and feeds extracted values back into the user profile.
- **Financial engines** compute the health score, goal milestones, tax comparison, and portfolio recommendation.
- **Report generator** produces the final structured advisory output and exports a PDF for download.

## Current deployment shape

- **Runtime**: single-process local FastAPI app
- **State**: in-memory session storage
- **LLM provider**: Groq via OpenAI-compatible API
- **Document parsing**: local PDF text extraction
- **Report output**: generated PDF file returned by the backend
