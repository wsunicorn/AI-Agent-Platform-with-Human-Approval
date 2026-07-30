# Frontend Spec

## Design Read

A dense, dark-themed B2B operations dashboard for support teams and
managers — built with Radix Themes (`appearance="dark"`, teal accent) over
Tailwind v4 utility classes.

## Frontend Stack (what's actually wired up)

- React 19, TypeScript, Vite 7, Tailwind CSS v4
- `@radix-ui/themes` for the base theme + individual Radix primitives
  (`Dialog`, `DropdownMenu`, `Tabs`)
- TanStack Query v5 for all server-state fetching/caching/invalidation
- `@phosphor-icons/react` for icons
- `@uiw/react-codemirror` for the approval payload JSON editor

Installed but **not currently used** by any shipped page: `@tanstack/react-router`,
`@tanstack/react-table`, `react-hook-form` + `@hookform/resolvers` + `zod`,
`zustand`, `motion`, `recharts`. See [`TECH_STACK.md`](TECH_STACK.md).

## Navigation model — no URL routing

`frontend/src/app/App.tsx` holds all navigation state in `useState`:
`currentPath` (a string like `"/tickets"`, used only to pick a top-level page)
plus `activeTicketId` / `activeAgentRunId` / `activeApprovalId` for drill-down
views. There is no `<Router>`, no `window.history` usage, and no
`react-router`/`@tanstack/react-router` involved. Practical consequences:

- Reloading the page always returns to the Ticket Inbox — you cannot deep
  link to a specific ticket, run, or approval.
- The browser back/forward buttons do nothing useful inside the app.
- Sharing a URL to a specific approval or ticket isn't possible today.

If you want real deep links, wiring up `@tanstack/react-router` (already a
dependency) to mirror the current `currentPath`/`activeXId` state is the
natural next step.

## Main Layout

```text
left sidebar navigation (Sidebar.tsx)
top status bar (TopBar.tsx)
main content area, max-width constrained, single column drill-down
```

There's no split-pane / right contextual panel in the current implementation
— each screen is a single stacked column; drill-down (ticket → detail → run
timeline, or approval → detail) replaces the whole content area rather than
opening a side panel.

## Screens (as actually implemented)

### Ticket Inbox (`pages/TicketInbox.tsx`)

List of tickets with status/priority. Clicking a row opens Ticket Detail.

### Ticket Detail (`pages/TicketDetail.tsx`)

Original message, extracted entities, intent/priority, and a way to start a
support-agent run / view its timeline (`onViewRun`).

### Approval Queue (`pages/ApprovalQueue.tsx`)

- Status filter tabs (`""`/all, `pending_review`, `approved`, `rejected`,
  `executed`).
- **Polls every 5 seconds** (`refetchInterval: 5000`) — it does *not* open
  `/ws/approvals`, even though that WebSocket channel exists and works on the
  backend (`app/api/websockets.py`, `frontend/src/lib/websocket.ts:createApprovalSocket`
  is exported but never called from any page). So approval state can lag up
  to 5s, and there is no push notification for a brand-new approval landing
  in the queue.
- Per-row Approve/Reject/Execute buttons, each a `useMutation`; on failure the
  row shows an inline error message from the normalized API error envelope
  (see [`API_DESIGN.md`](API_DESIGN.md)).
- Reviewer identity is hardcoded to the string `"admin"` on every mutation —
  there's no real user/session, so the audit trail's `reviewer` field never
  reflects who actually clicked the button.

### Approval Detail (`pages/ApprovalDetail.tsx`)

Proposed payload, editable payload (CodeMirror JSON editor), a simple
line-by-line added/removed/unchanged diff against the proposed payload once
edited, risk reason, and Approve/Edit-and-approve/Reject/Execute actions. Same
5-second-poll/no-WebSocket and hardcoded-reviewer caveats as the queue above.

### Agent Run Timeline (`pages/AgentRunTimeline.tsx`)

Live-updating via `createAgentRunSocket(runId)` (the one page that *does* use
a WebSocket): any non-`pong` event on that run's topic invalidates the run and
tool-call queries, triggering a refetch. Shows run outcome summary, completed
deliveries (email/CRM-note/report-export), pending approvals inline, the
original input, and a chronological list of tool calls with expandable
input/output JSON. Tool-call status styling distinguishes `completed`
(green), `failed`/`denied` (red), and everything else — including
`waiting_for_approval` — as amber/in-progress.

### Knowledge Base Manager (`pages/KnowledgeBase.tsx`)

Document list (title, chunk count, "indexed" status badge — see caveat
below), a create-document form (title/content/type), delete, and a search
test panel that calls `POST /knowledge-documents/search` directly. The
document-type selector must use one of the real backend enum values —
`policy`, `faq`, `playbook`, `macro`, `report_template` — a document type
outside that set is rejected by Pydantic validation server-side. There is no
per-chunk preview UI; only a chunk count is shown. The "indexed" status badge
is not a real state machine — `KnowledgeDocument.status` is a hardcoded
property that always returns `"indexed"` (`app/models/knowledge.py`); there is
no pending/processing/failed indexing state anywhere in the data model
(ingestion is synchronous inside the create request, so by the time the
document appears in the list it's already fully indexed).

### Audit Log Explorer (`pages/AuditLogs.tsx`)

Filterable list (actor, event type, entity type), each row rendered with a
server-computed human-readable `message` and `severity`
(`app/api/audit_logs.py:_audit_message`/`_audit_severity`) rather than raw
`event_type` strings.

### Settings (`pages/Settings.tsx`)

Tabs for Model Configs, Tools, and Guardrail Policies, all reading/writing
`/settings/*`. Tool and guardrail-policy edits take effect immediately in the
running process (they mutate the shared `TOOL_SENSITIVITY_CATALOG`). Model
config edits are stored but **do not** change what `ModelRouter` actually
calls — see [`LLM_AND_RETRIEVAL.md`](LLM_AND_RETRIEVAL.md). There is no
per-tool enable/disable enforcement wired to the executor either; the
`enabled` field round-trips through the API but `PolicyEngine`/`ToolExecutor`
don't check it.

## Required UI States (implemented via `components/ui/States.tsx`)

`LoadingState`, `EmptyState`, `ErrorState` (with optional retry), plus
per-status badges (`StatusBadge.tsx`) for waiting/approved/rejected/failed/
completed. Mutation-level errors (a failed approve/reject/execute/edit) show
as an inline red banner near the action, not a full-page `ErrorState`.

## UX Notes That Still Hold

- Approval states are visually distinct (color-coded badges) and risk reasons
  are always shown inline, never hidden behind a hover.
- The audit trail is one click away from any run or approval (Audit Log
  Explorer filters by entity/actor/action).
