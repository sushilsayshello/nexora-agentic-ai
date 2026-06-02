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

