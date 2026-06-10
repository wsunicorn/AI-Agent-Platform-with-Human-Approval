# Frontend Spec

## Design Read

This is a serious B2B operations dashboard for support teams and managers. It should feel trustworthy, fast, dense, and review-friendly.

Use taste-skill principles for frontend polish, but adapt them to product UI instead of marketing pages.

## Frontend Stack

- React
- TypeScript
- Vite
- Tailwind CSS v4
- Radix UI or shadcn/ui
- TanStack Query
- TanStack Router or React Router
- TanStack Table
- React Hook Form
- Zod
- Zustand
- Motion
- CodeMirror 6 or Monaco Editor

## Main Layout

Recommended desktop layout:

```text
left sidebar navigation
top status bar
main split-pane work area
right contextual panel
```

## Primary Screens

### Ticket Inbox

- Ticket list.
- Priority filter.
- Intent filter.
- Status filter.
- Live updates.
- Selected ticket preview.

### Ticket Detail

- Original message.
- Extracted entities.
- Intent and priority.
- Retrieved policy sources.
- Draft response.
- Proposed tool actions.
- Agent timeline.

### Approval Queue

- Pending approvals.
- Risk reason.
- Tool name.
- Created time.
- Reviewer actions.
- Live status changes.

### Approval Detail

- Proposed payload.
- Editable payload.
- Payload diff.
- Risk reason.
- Policy references.
- Approve, reject, edit, execute actions.

### Agent Run Timeline

- Step started.
- Step completed.
- Tool called.
- Tool failed.
- Approval created.
- Approval executed.
- Final output.

### Knowledge Base Manager

- Document list.
- Upload or paste policy docs.
- Indexing status.
- Chunk preview.
- Search test panel.

### Audit Log Explorer

- Search and filters.
- Actor.
- Event type.
- Entity type.
- Before and after state.
- Timestamp.

### Settings

- Model config.
- Tool registry config.
- Guardrail policy config.
- Local model status.

## Required UI States

- Loading.
- Empty.
- Error.
- Streaming/running.
- Retrying.
- Waiting for approval.
- Approved.
- Rejected.
- Failed.
- Completed.

## UX Rules

- First screen must be the product, not a landing page.
- Avoid generic AI-purple gradient visuals.
- Prefer dense but readable support-operations layouts.
- Keep approval states visually obvious.
- Keep audit trail close to AI recommendations.
- Use keyboard-friendly reviewer workflows.
- Do not hide risk reasons behind hover-only UI.
- Use accessible focus states and contrast.

## Suggested Routes

```text
/
/tickets
/tickets/:ticketId
/agent-runs/:runId
/approvals
/approvals/:approvalId
/knowledge
/audit-logs
/settings/models
/settings/tools
/settings/guardrails
```

