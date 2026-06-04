# Nexora Sentinel Unified Software

This is the combined runnable version made from the uploaded Nexora folders.
https://sushilsayshello.github.io/nexora-agentic-ai/


## Best source choice

- Best frontend concept: `Nexora Agentic AI(1).zip` because it had the cleanest React-style product story and sections.
- Best backend/API: `nexora_sentinel_production_ready(1).zip` because it already had a working FastAPI server, mandate engine, PayPal/Bloomreach/Exponea endpoints, audit trail, personas and merchant APIs.
- Best architecture/prototype reference: `nexora-sentinel-v2 (1).zip` because it included Docker-style structure, LangGraph-style backend files and a graph image.

This unified folder uses the working backend as the base and a clean production-style frontend that runs without npm. That makes it easier to demo quickly on Windows.

## What is included

- Customer login and merchant login
- Standard, Deaf/HH, low vision, cognitive support and motor access personas
- 12 agentic AI scenarios
- AI signal detection, recommendation and risk scoring
- Human mandate approval before payment
- PayPal order creation through backend only
- Bloomreach/Exponea message trigger through backend only
- Guardian approval flow endpoints
- Merchant dashboard
- Audit trail and audit stats
- Backend-only `.env` for credentials/API keys

## Security rule

Credentials and API keys are stored only in `backend/.env`. The frontend does not contain PayPal, Bloomreach, Exponea, Gemini, OpenAI or other secret keys.

Do not push `backend/.env` to GitHub. Use `.env.example` for public repositories.

## Windows run steps

1. Extract this ZIP.
2. Open the folder in VS Code.
3. Run `scripts/setup_windows.bat` once.
4. Run `scripts/run_all.bat`.
5. Open `http://localhost:3000`.
6. Backend docs: `http://localhost:8000/docs`.

## Logins

- Standard customer: `customer@nexora.ai` / `Customer@123`
- Deaf / HH customer: `deaf@nexora.ai` / `Customer@123`
- Low vision customer: `vision@nexora.ai` / `Customer@123`
- Cognitive support customer: `cognitive@nexora.ai` / `Customer@123`
- Motor access customer: `motor@nexora.ai` / `Customer@123`
- Merchant admin: `admin@nexora.ai` / `Nexora@123`

## Demo flow

Each scenario runs:

1. Signal detected
2. Agent explains reason
3. Backend creates recommendation
4. Risk council evaluates
5. Human mandate is requested
6. User approves or rejects
7. PayPal order runs only after approval
8. Bloomreach/Exponea action triggers
9. Audit trail and merchant dashboard update

## Folder layout

```text
backend/main.py        FastAPI app
backend/.env          backend-only credentials/API keys
backend/.env.example  safe template
frontend/index.html   browser UI, no secrets
scripts/*.bat         Windows setup/run scripts
requirements.txt      Python dependencies
```
