# MVP Scope

## Product Goal

Build a human-in-the-loop AI support operations platform that can classify tickets, retrieve policies, draft responses, call tools, and require human approval before sensitive actions are executed.

## MVP Positioning

The MVP is not a generic chatbot. It is an AI operations dashboard with explicit approval controls, audit logs, and deterministic guardrails.

## Primary User Flow

```text
support ticket
-> intent classification
-> priority detection
-> entity extraction
-> policy retrieval
-> response draft
-> action planning
-> policy gate
-> approval queue for sensitive actions
-> approved execution
-> audit log
```

## Must Have

- Ticket, email, or free-text input.
- Support Agent mode.
- Workflow Automation mode as a basic secondary flow.
- Intent classification.
- Priority detection.
- Entity extraction.
- Knowledge base retrieval.
- Response drafting.
- LangGraph workflow orchestration.
- Tool registry.
- Tool input/output validation with Pydantic.
- Action sensitivity model: safe, approval-required, blocked.
- Human approval queue.
- Audit log for every tool call and approval decision.
- FastAPI REST API.
- FastAPI WebSocket API.
- Redis Pub/Sub and Redis Streams for realtime events.
- PostgreSQL as primary database.
- pgvector for vector search.
- React dashboard.
- Mock integrations for email, CRM, refund, and report export.
- Docker Compose for local development.

## Should Have

- Local LLM fallback through Ollama.
- Gemini free-tier primary model for demo and development.
- Hybrid retrieval with full-text search plus vector search.
- Reranking before context is sent to the LLM.
- Payload diff view before approval.
- Agent run timeline.
- Model and tool configuration screen.
- Seed demo data.
- End-to-end tests for the approval workflow.

## Not In MVP

- Real payment-provider refunds.
- Real customer data ingestion.
- Production Zendesk, Salesforce, Gmail, or Slack integrations.
- Multi-tenant billing.
- Advanced role-based access control.
- Agent marketplace.
- Autonomous execution of sensitive actions.
- Large analytics warehouse.
- Production-grade SSO.

## MVP Success Criteria

- A refund ticket can be submitted.
- The agent classifies the ticket and extracts the order ID.
- The agent retrieves a relevant refund policy.
- The agent drafts a response.
- The agent proposes a customer email action.
- The email action is queued for approval instead of being sent.
- A human reviewer can edit and approve the action.
- The approved mock email action executes.
- The audit log shows every step.
- The dashboard receives live updates through WebSockets.

