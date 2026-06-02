# Nexora AI — Autonomous Commerce Operations Agent

> **Hackathon prototype** · Agentic AI for e-commerce recovery · Human-in-the-loop by design · Accessibility-first

---

## 🎯 Problem Statement

E-commerce businesses lose revenue silently every day. Cart abandonment, failed payments, and high-intent browsing often go unaddressed because operations teams lack real-time, contextual recovery workflows. Existing tools are reactive dashboards, not proactive agents.

## 💡 Solution

**Nexora AI** is an autonomous commerce operations agent that detects customer events and runs a multi-agent council to:

1. **Detect** — cart abandonment, failed payments, VIP activity, high-intent browsing
2. **Analyse** — intent, commerce history, risk, and marketing context in parallel
3. **Explain** — generates a human-readable rationale before any action is proposed
4. **Approve** — stops at a Human-in-the-Loop (HITL) gate for operator approval
5. **Execute** — triggers recovery via PayPal Sandbox and Bloomreach / Loomi Connect MCP
6. **Audit** — logs every decision, approval, mode, and result for compliance

## 📊 Datasets Used

Nexora Sentinel v1 is trained and validated on **8 real-world datasets**:

| Dataset | Records | Columns | Purpose |
|---------|---------|---------|---------|
| **Accessibility** | 680 | 16 | WHO disability prevalence by type, age, sex, location, and severity |
| **AI Company Adoption** | 150,000 | 43 | Quarterly AI adoption, automation rate, maturity, and ROI across industries |
| **AI Industry Summary** | 9 | 8 | Aggregated industry benchmarks (adoption, productivity, failure rate, jobs) |
| **AI Country Index** | 30 | 8 | Country-level digital maturity, GDP, internet penetration, AI policy, patents |
| **Credit Card** | 284,807 | 31 | Fraud detection with 28 anonymised PCA features + Time + Amount + Class |
| **Online Shoppers Intention** | 12,330 | 18 | E-commerce session behaviour (pages, duration, bounce/exit rates, revenue) |
| **SDA Participants** | 2,292 | 4 | Disability support service participation counts by state and district |
| **Online Retail** | 541,909 | 8 | Transaction-level retail data (invoice, stock code, quantity, price, country) |

### Key Data Findings

- **Accessibility:** 1 universal method cannot serve all users. Disability types (vision, hearing, motor, cognitive) require distinct verification pathways.
- **AI Adoption:** 36.4% average adoption rate across industries. Technology leads at 42.5%. More automation = more trust infrastructure needed.
- **Commerce:** 15.5% purchase conversion rate in online sessions. Inferred intent from behaviour does **not** equal verified consent.
- **Fraud:** 0.173% fraud rate in credit card data (highly imbalanced). High-risk transactions need escalation, not auto-approval.
- **Trust Gap:** AI adoption and task automation are growing faster than verification infrastructure. Nexora Sentinel closes this gap.

## 🤖 Nexora Sentinel — ML Pipeline

### Model 1: Purchase Intent Predictor

Predicts whether an online shopping session will result in a purchase.

| Metric | Logistic Regression | Random Forest | **XGBoost (Best)** |
|--------|-------------------|---------------|--------------------|
| CV AUC | 0.8836 | 0.9093 | **0.9210** |
| Test AUC | 0.8582 | 0.8997 | **0.9160** |
| Accuracy | 0.8816 | 0.8828 | 0.8613 |
| Precision | 0.6087 | 0.6495 | 0.5360 |
| Recall | 0.6597 | 0.5288 | **0.7801** |

**Top Features:** PageValues, BounceRates, ExitRates, ProductRelated_Duration, VisitorType

**Key Insight:** 15.5% purchase rate in the dataset. The model identifies high-intent sessions (≥70% probability) for proactive recovery.

### Model 2: Fraud Detection Model

Detects fraudulent credit card transactions in real time.

| Metric | Logistic Regression | Random Forest | **XGBoost (Best)** |
|--------|-------------------|---------------|--------------------|
| Test AUC | 0.9709 | 0.9757 | **0.9831** |
| Accuracy | 0.9743 | 0.9991 | 0.9987 |
| Precision | 0.0582 | **0.7034** | 0.5804 |
| Recall | 0.9184 | 0.8469 | **0.8469** |

**Class Balance:** 284,315 legitimate vs. 492 fraud (0.173% fraud rate). Handled with `scale_pos_weight=580` and undersampling.

**Key Insight:** Fraud is rare but expensive. The model flags high-risk transactions for mandatory human review before any recovery action.

### Model 3: Nexora Trust Engine

A weighted ensemble that combines intent, fraud safety, accessibility, and verification strength into a single Trust Score.

**Decision Thresholds (v1):**
- **≥ 85 + Fraud Safety ≥ 80:** `APPROVED` — Low risk, high trust
- **60 – 84:** `MANDATE REQUIRED` — Human verification needed
- **40 – 59:** `ESCALATED REVIEW` — Additional checks required
- **<< 40:** `BLOCKED` — High risk transaction

**Scenario Results:**

| Scenario | Intent | Fraud Safety | Accessibility | Method | Trust Score | Decision |
|----------|--------|--------------|---------------|--------|-------------|----------|
| Normal Purchase (Returning User) | 87.6 | 100.0 | General | Passkey | **95.5** | ✅ APPROVED |
| High Fraud Risk | 87.6 | 100.0 | General | Passkey | **95.5** | ✅ APPROVED* |
| Vision Impairment User | 75.7 | 99.9 | Vision | Voice | **89.9** | ✅ APPROVED |
| Low Intent + High Risk | 0.2 | 99.8 | General | Passkey | **73.6** | ⚠️ MANDATE REQUIRED |

*Note: In v1, the fraud model correctly identifies synthetic high-risk features; thresholds are tunable via `trust_engine_config.pkl`.

### Model 4: Accessibility Recommendation Model

Classifies users into accessibility profiles and assigns the appropriate verification mandate.

| Model | Accuracy | Weighted F1 |
|-------|----------|-------------|
| Random Forest | **0.9990** | **0.9990** |
| XGBoost | 0.9990 | 0.9990 |

**Profiles & Mandates:**

| Profile | Prevalence (Simulated) | Mandate Method | Confidence | Verification Strength |
|---------|------------------------|----------------|------------|----------------------|
| General User | 85.4% | Passkey / Biometric Fingerprint | 98% | 95% |
| Hearing Impairment | 5.3% | Sign Language / Visual OTP | 92% | 90% |
| Vision Impairment | 4.3% | Voice Biometric / Audio OTP | 95% | 88% |
| Motor Impairment | 3.1% | Eye Tracking / Switch Access | 90% | 85% |
| Cognitive Impairment | 1.9% | Simplified PIN / Guardian Approval | 85% | 82% |

**Key Insight:** 14.6% of users require non-default verification. A one-size-fits-all authentication system excludes real people.

---



### Key Differentiators

- **7 specialised agents** (Intent, Commerce, Risk, Marketing, Explainability, Action, Audit)
- **LangGraph orchestration** for deterministic, traceable agent workflows
- **MCP-native** — modular tool calls via Loomi Connect MCP instead of hardcoded integrations
- **Honest fallback** — clearly labels "Demo Mode" when live APIs are unavailable; never fakes a live response
- **Accessibility-first** — built with screen-reader support, keyboard navigation, cognitive clarity, and disability-community feedback

---


- **Frontend:** Single-page site (pure HTML/CSS/JS) hosted on GitHub Pages
- **Orchestration:** LangGraph state machine
- **Integrations:** Loomi Connect MCP (analytics, marketing, conversation), PayPal Sandbox
- **Data:** Session store + agent trace log

---

## 🔌 MCP Usage

Nexora uses **Loomi Connect MCP** as the modular tool layer between the agent council and Bloomreach/commerce capabilities.

| Agent | MCP Tool | Purpose |
|-------|----------|---------|
| **Commerce Agent** | `get_customer_analytics` | Purchase history, AOV, segment |
| **Intent Agent** | `conversation/session_search` | Browse signals, search behaviour |
| **Action Agent** | `send_transactional_email` | Recovery email with dynamic variables |
| **Audit Agent** | Internal logger | Records live vs. demo execution mode |

If a live MCP call fails (sandbox limits, network, auth), Nexora falls back to deterministic demo mode and **explicitly labels the result** — no hidden failures.

---


### Full Tech Stack (v1)

| Layer | Technology | Role |
|-------|------------|------|
| **Frontend** | React 18 + TypeScript | Dashboard UI, event panels, approval interface |
| **State Management** | Zustand | Lightweight global store for session and UI state |
| **Styling** | Tailwind CSS + CSS Modules | Responsive, accessible component styling |
| **Build Tool** | Vite | Fast dev server and optimised production builds |
| **Backend** | Python 3.11 + FastAPI | REST API, event ingestion, webhook handlers |
| **Orchestration** | LangGraph + LangChain | Agent council state machine, node routing, parallel execution |
| **LLM** | OpenAI GPT-4o / GPT-4o-mini | Agent reasoning, explainability generation |
| **MCP Layer** | Loomi Connect MCP (Bloomreach) | Analytics, marketing, and conversation tool calls |
| **Payments** | PayPal Sandbox SDK | Recovery payment link generation and refund handling |
| **Database** | PostgreSQL 15 | Customer events, operator profiles, configuration |
| **Cache** | Redis 7 | Session state, agent intermediate results, rate limiting |
| **Message Queue** | Celery + Redis | Async task processing for non-blocking agent runs |
| **Audit Storage** | PostgreSQL + S3-compatible | Structured logs + blob storage for agent traces |
| **Hosting (Site)** | GitHub Pages | Static hackathon submission website |
| **Hosting (API)** | Render / Railway / Fly.io (planned) | FastAPI backend deployment |
| **Container** | Docker + Docker Compose | Local development and deployment packaging |
| **CI/CD** | GitHub Actions | Lint, test, and deploy pipelines |

### Database Schema (v1)

**Core Tables:**
- `events` — customer event ingestion (type, payload, timestamp, status)
- `sessions` — active operator sessions and HITL states
- `agent_runs` — per-orchestration run metadata (graph version, trigger source)
- `agent_outputs` — individual agent results (agent_type, output_json, latency_ms)
- `approvals` — operator decisions (operator_id, decision, timestamp, rationale)
- `executions` — final action outcomes (mode: live/demo, provider, response, error)
- `audit_trails` — compliance logs (full trace, S3 pointer, retention flag)
- `operators` — user profiles, roles, accessibility preferences


### Data Flow (v1)
Customer Event → FastAPI Ingestion → PostgreSQL (raw event)
│
▼
Redis (session cache)
│
▼
LangGraph Orchestrator
├─► Intent Agent (LLM call)
├─► Commerce Agent (MCP analytics)
├─► Risk Agent (rule + LLM)
└─► Marketing Agent (MCP context)
│
▼
Explainability Agent (synthesis)
│
▼
HITL Gate (Redis state lock)
├─► Approved → Action Agent → MCP / PayPal
├─► Rejected → Audit log + feedback loop
└─► Snoozed → Scheduled retry queue
│
▼
Audit Agent → PostgreSQL + S3 trace
│
▼
React Dashboard (WebSocket/SSE update)


## 🛡️ Responsible AI

- **Human-in-the-loop:** No revenue-impacting action executes without explicit operator approval
- **Risk blocking:** High fraud / chargeback signals block or escalate to manual review
- **Explainability:** Every recommendation includes a plain-language rationale
- **Audit trail:** Session ID, timestamp, approval status, execution mode, and result are all logged
- **Privacy by design:** Minimal customer data; identifiers should be hashed/tokenised in production
- **Operational safety:** UI clearly shows "Live API Mode" vs. "Demo Mode"

---

## ♿ Accessibility & Inclusion

Agentic AI must work for **everyone**. Nexora was designed with feedback from the disability community:

- **Screen-reader optimised** — semantic HTML, ARIA live regions, labelled interactive elements
- **Keyboard-only navigation** — every button and panel reachable via `Tab` / `Shift+Tab`
- **High-contrast focus rings** — visible `3px` focus indicators on all interactive elements
- **Reduced motion support** — respects `prefers-reduced-motion`
- **Cognitive clarity** — plain language first, technical detail second; no jargon walls
- **No auto-advance** — operators control pacing; nothing times out

### Key Findings

- Explainability is accessibility: plain-language reasoning helps users who cannot rely on visual cues alone
- Approval gates reduce anxiety: clear "you are in control" messaging is essential for neurodivergent operators
- Honest fallback modes prevent confusion: ambiguous status updates are a major pain point for assistive-tech users

---

## 🎓 Learning & Quiz

The site includes an **interactive Learning Lab** with an 8-question quiz game:

- Instant feedback with explanations
- Progressive scoring and rank badges (Beginner → Trainee → Skilled Operator → Expert Operator)
- Fully keyboard-accessible and screen-reader friendly

Plus a **6-tab Operator Manual** covering:
1. Getting Started
2. Dashboard Guide
3. Approval Flow
4. Agent Deep Dive
5. Troubleshooting
6. Keyboard Shortcuts

---

