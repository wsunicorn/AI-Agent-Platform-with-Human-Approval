# Case Study & Demo Video Script: B2B AI Agent Platform

## 1. Case Study Summary

### The Problem
Support operations teams are under constant pressure to automate responses and actions using AI, but fully autonomous AI agents present severe risks:
1. **Financial Risk**: Autonomously approving incorrect refunds or discounts.
2. **Operational Risk**: Accidental data deletion or triggering non-compliant customer escalations.
3. **Reputational Risk**: AI agents drafting or sending emails that are tone-deaf or inaccurate.

### The Solution: HumanGate AI
We built a dual-workflow B2B AI Agent Platform that keeps a "human-in-the-loop" for all sensitive operations, ensuring safety without sacrificing automation speed:
1. **Intent & Priority Triage**: Fast, automated parsing of incoming tickets using Gemini models with local Ollama fallback.
2. **Retrieval-Augmented Generation (RAG)**: Safe retrieval of company policy docs with Reciprocal Rank Fusion (RRF) and LLM-based reranking.
3. **Guardrail Policy Engine**: Automatically classifies proposed tools into **Safe** (executed immediately), **Approval-Required** (paused for human review), or **Blocked** (denied completely).
4. **Editable Payloads**: Reviewers can view visual JSON diffs and edit payloads (e.g., modifying email text or refund amounts) directly before approval/execution.
5. **Real-time Synchronization**: WebSocket manager broadcasts live execution updates and approval alerts to the React frontend.
6. **Durable Audit Logging**: Every policy decision, approval state transition, and tool execution is securely stored for compliance auditing.

### Key Metrics & Outcomes
- **100% Guardrail Enforced**: Zero sensitive actions can bypass server-side verification.
- **Zero Double-Execution**: Cryptographically backed locking prevents simultaneous execution of identical actions.
- **Resilient Fallbacks**: Smooth, automated transition to local LLM engines if API quotas are exhausted.

---

## 2. Demo Video Script

**Target Duration**: 3 minutes

### Scene 1: Introduction (0:00 - 0:30)
- **Visual**: Show the React Dashboard on the Ticket Inbox screen. Click on "New Ticket" and show the clean dark-mode design.
- **Voiceover**: 
  > "Welcome to HumanGate AI, a B2B platform designed to safely automate customer support operations. By integrating LangGraph agent workflows with a robust guardrail policy engine, we keep humans in the loop for sensitive actions while automating routine triage."

### Scene 2: The Ticket & Support Agent Run (0:30 - 1:15)
- **Visual**: Select the ticket "Refund request for order #12345" from Maya Chen. Click **Run Agent**. Show the screen transitioning to the **Agent Execution Timeline**. Watch the timeline steps build in real-time.
- **Voiceover**: 
  > "Let's open a new ticket from Maya Chen requesting a refund for order 12345. Clicking 'Run Agent' kicks off our LangGraph workflow. The agent normalizes the text, classifies the intent as a refund, retrieves relevant policies from our PostgreSQL knowledge base, and plans tool calls. Because sending an email is classified as a sensitive action, the workflow pauses, and a human approval request is generated."

### Scene 3: Approving & Editing Actions (1:15 - 2:15)
- **Visual**: Click on the **Approvals** tab in the sidebar. Click on the pending `send_email` request. Show the proposed payload. Click **Edit Payload**, change the email body slightly, and click **Save**.
- **Voiceover**: 
  > "Navigating to the Approvals Queue, we see the pending request. We can review the proposed JSON payload and see the risk warning. If the draft needs adjustment, we can click 'Edit Payload', edit the text directly in the CodeMirror editor, save, and then click 'Approve'. Playwright E2E tests confirm this visual editing and state machine work flawlessly."

### Scene 4: Execution & Audit Logging (2:15 - 3:00)
- **Visual**: Click **Execute Action**. Show the badge update to `executed`. Navigate to **Audit Logs** to show the recorded `approval.created`, `approval.approved`, and `tool_call.completed` events.
- **Voiceover**: 
  > "Clicking 'Execute' runs the tool safely under Redis lock to prevent duplicate triggers. The timeline updates instantly. Finally, looking at our Audit Log Explorer, every single state change, reviewer action, and tool execution has been durably recorded for complete operational transparency. Safe, fast, and fully auditable support automation."
