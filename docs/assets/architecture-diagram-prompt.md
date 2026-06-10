# Architecture Diagram Image Prompt

Use this prompt to regenerate the architecture diagram with ChatGPT Image or another image generation tool.

```text
Use case: infographic-diagram
Asset type: technical architecture diagram for a software project documentation page
Primary request: Create a clean modern architecture diagram for an AI Agent Platform with Human Approval.
Style/medium: polished technical product architecture infographic, flat vector-like diagram, white background, sharp lines, readable labels, professional B2B SaaS documentation style.
Composition/framing: landscape 16:9 layout. Arrange as layered system architecture from left to right and top to bottom.

Text (verbatim, must be readable):
Title: "AI Agent Platform with Human Approval"

Left column: "React Dashboard" with sublabels "Ticket Inbox", "Approval Queue", "Audit Log", "Settings".

Center top: "FastAPI REST + WebSocket API".

Center middle: "LangGraph Workflows" with sublabels "Classify", "Retrieve", "Draft", "Plan", "Approval Interrupt".

Center lower: "Guardrail Policy Engine" with decisions "Safe", "Approval Required", "Blocked".

Right column: "Tool Executor" with tools "Search KB", "Draft Email", "Mock Email", "Mock CRM", "Report Export".

Bottom row: "PostgreSQL + pgvector" with sublabels "Tickets", "Approvals", "Audit Logs", "Knowledge Chunks"; "Redis Streams + Pub/Sub" with sublabels "Realtime Events", "Worker Queue", "Locks"; "LLM Gateway" with sublabels "Gemini Free", "Ollama Local", "Model Router".

Add arrows:
React Dashboard -> FastAPI
FastAPI -> LangGraph
LangGraph -> Guardrail Policy Engine
Guardrail Policy Engine -> Tool Executor
Tool Executor -> PostgreSQL
LangGraph -> Redis
LangGraph -> LLM Gateway
FastAPI -> Redis -> React Dashboard for realtime updates

Color palette: neutral white and zinc gray base, one restrained teal accent for approval/realtime paths, amber accent for approval-required, red accent for blocked. Avoid purple AI gradients.

Constraints: Make all text clean and legible. Use simple rectangular modules with subtle rounded corners. No decorative characters, no people, no stock imagery, no watermark. Avoid misspellings.
```

