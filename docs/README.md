# Documentation Index

This folder turns the project idea into implementation-ready documents.

## Source Brief

- Main idea file: [`../AI_AGENT_PLATFORM_IDEA.md`](../AI_AGENT_PLATFORM_IDEA.md)

## Core Docs

- [`MVP_SCOPE.md`](MVP_SCOPE.md): What the first version must and must not include.
- [`TECH_STACK.md`](TECH_STACK.md): Final technology choices and why they fit this system.
- [`ARCHITECTURE.md`](ARCHITECTURE.md): System architecture, service boundaries, and event flow.
- [`assets/architecture-diagram-chatgpt-image.png`](assets/architecture-diagram-chatgpt-image.png): Generated architecture diagram image.
- [`assets/architecture-diagram-prompt.md`](assets/architecture-diagram-prompt.md): Prompt used to generate the diagram.
- [`DATA_MODEL.md`](DATA_MODEL.md): PostgreSQL tables and core relationships.
- [`API_DESIGN.md`](API_DESIGN.md): REST and WebSocket API contract draft.
- [`AGENT_WORKFLOWS.md`](AGENT_WORKFLOWS.md): LangGraph workflows for support and automation modes.
- [`GUARDRAILS_AND_APPROVALS.md`](GUARDRAILS_AND_APPROVALS.md): Human approval, action sensitivity, and policy gates.
- [`LLM_AND_RETRIEVAL.md`](LLM_AND_RETRIEVAL.md): Gemini-first LLM routing, local model fallback, and RAG design.
- [`FRONTEND_SPEC.md`](FRONTEND_SPEC.md): React dashboard UX, screens, components, and states.
- [`DEVELOPMENT_SETUP.md`](DEVELOPMENT_SETUP.md): Local development setup plan.
- [`DEMO_SCENARIOS.md`](DEMO_SCENARIOS.md): Demo flows and sample scenarios.
- [`PROJECT_BOARD.md`](PROJECT_BOARD.md): Lightweight local issue/project board.
- [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md): Full project progress checklist.

## Recommended Build Order

1. Read `MVP_SCOPE.md`.
2. Set up the backend from `TECH_STACK.md` and `DEVELOPMENT_SETUP.md`.
3. Implement the data model from `DATA_MODEL.md`.
4. Build guardrails and approval logic from `GUARDRAILS_AND_APPROVALS.md`.
5. Implement LangGraph workflows from `AGENT_WORKFLOWS.md`.
6. Add LLM and retrieval from `LLM_AND_RETRIEVAL.md`.
7. Build the React dashboard from `FRONTEND_SPEC.md`.
8. Validate the product through `DEMO_SCENARIOS.md`.
9. Track all progress in `PROJECT_CHECKLIST.md`.
