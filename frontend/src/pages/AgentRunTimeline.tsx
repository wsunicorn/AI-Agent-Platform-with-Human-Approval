/** Agent Run Timeline page. */

import {
  ArrowLeft,
  CircleNotch,
  CheckCircle,
  EnvelopeSimple,
  Hammer,
  Hourglass,
  Play,
  Prohibit,
  WarningCircle,
  XCircle,
} from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { ErrorState, LoadingState } from "../components/ui/States";
import { StatusBadge } from "../components/ui/StatusBadge";
import { TimeAgo } from "../components/ui/TimeAgo";
import { cancelAgentRun, fetchAgentRun, fetchToolCalls } from "../lib/api";
import { createAgentRunSocket } from "../lib/websocket";
import type {
  AgentRun,
  RunActionSummary,
  RunApprovalSummary,
  ToolCall,
} from "../types/models";

interface AgentRunTimelineProps {
  runId: string;
  onBack: () => void;
}

const WAITING_APPROVAL_STATUSES = new Set([
  "proposed",
  "pending_review",
  "approved",
  "edited",
]);

export function AgentRunTimeline({ runId, onBack }: AgentRunTimelineProps) {
  const queryClient = useQueryClient();
  const [expandedCalls, setExpandedCalls] = useState<Set<string>>(new Set());

  const { data: run, isLoading: isLoadingRun, error: runError } = useQuery<AgentRun>({
    queryKey: ["agent-run", runId],
    queryFn: () => fetchAgentRun(runId),
  });

  const {
    data: toolCalls,
    isLoading: isLoadingCalls,
    error: callsError,
  } = useQuery<ToolCall[]>({
    queryKey: ["tool-calls", runId],
    queryFn: () => fetchToolCalls(runId),
    enabled: !!run,
  });

  useEffect(() => {
    const ws = createAgentRunSocket(runId);
    ws.connect();

    const unsubscribe = ws.subscribe(() => {
      queryClient.invalidateQueries({ queryKey: ["agent-run", runId] });
      queryClient.invalidateQueries({ queryKey: ["tool-calls", runId] });
    });

    return () => {
      unsubscribe();
      ws.disconnect();
    };
  }, [runId, queryClient]);

  const cancelMutation = useMutation({
    mutationFn: () => cancelAgentRun(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-run", runId] });
    },
  });

  const toggleExpand = (callId: string) => {
    setExpandedCalls((prev) => {
      const next = new Set(prev);
      if (next.has(callId)) next.delete(callId);
      else next.add(callId);
      return next;
    });
  };

  const isLoading = isLoadingRun || isLoadingCalls;
  const hasError = runError || callsError;

  if (isLoading) return <LoadingState message="Loading agent run timeline..." />;
  if (hasError || !run) return <ErrorState message="Failed to load agent run timeline" />;

  const finalOutput = run.final_output ?? {};
  const actions = finalOutput.actions ?? [];
  const deliveries = finalOutput.deliveries ?? [];
  const approvals = finalOutput.approvals ?? [];
  const pendingApprovals = approvals.filter((item) => WAITING_APPROVAL_STATUSES.has(item.status));
  const draftResponse = run.draft_response ?? finalOutput.draft_response;
  const isTerminal =
    run.status === "completed" || run.status === "failed" || run.status === "cancelled";

  return (
    <div>
      <div className="mb-6">
        <button
          onClick={onBack}
          className="mb-4 flex items-center gap-1.5 text-sm text-zinc-500 transition-colors hover:text-zinc-300"
        >
          <ArrowLeft size={14} />
          Back
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="flex items-center gap-2 text-xl font-semibold text-zinc-100">
              Agent Execution Timeline
              <span className="font-mono text-sm font-normal text-zinc-500">
                ({run.id.slice(0, 8)})
              </span>
            </h1>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Mode: {run.mode.replace(/_/g, " ")}
              </span>
              <StatusBadge status={run.status} />
              <TimeAgo date={run.created_at} />
            </div>
          </div>

          {!isTerminal && (
            <button
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
              className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/20 disabled:opacity-50"
            >
              Cancel Run
            </button>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-start gap-3">
              <span
                className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border ${
                  run.status === "failed"
                    ? "border-red-500/30 bg-red-500/10 text-red-400"
                    : run.status === "waiting_for_approval"
                      ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                      : "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                }`}
              >
                {run.status === "failed" ? (
                  <WarningCircle size={18} weight="bold" />
                ) : (
                  <CheckCircle size={18} weight="bold" />
                )}
              </span>
              <div className="min-w-0 flex-1">
                <h2 className="text-sm font-semibold text-zinc-200">Run Outcome</h2>
                <p className="mt-1 text-sm leading-relaxed text-zinc-400">
                  {finalOutput.summary ?? "The agent is still preparing the run summary."}
                </p>
                <MetricStrip counts={finalOutput.counts} />
              </div>
            </div>
          </section>

          {deliveries.length > 0 && (
            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-zinc-300">Completed Deliveries</h2>
              {deliveries.map((delivery, index) => (
                <DeliveryPanel key={delivery.id ?? index} delivery={delivery} />
              ))}
            </section>
          )}

          {pendingApprovals.length > 0 && (
            <section className="rounded-lg border border-amber-500/25 bg-amber-500/5 p-4">
              <div className="flex items-start gap-3">
                <Hourglass size={18} className="mt-0.5 shrink-0 text-amber-400" weight="fill" />
                <div>
                  <h2 className="text-sm font-semibold text-amber-300">
                    Waiting for Human Decision
                  </h2>
                  <div className="mt-2 space-y-1">
                    {pendingApprovals.map((approval) => (
                      <ApprovalLine key={approval.id} approval={approval} />
                    ))}
                  </div>
                </div>
              </div>
            </section>
          )}

          <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="mb-3 text-sm font-semibold text-zinc-300">Run Input</h2>
            <p className="whitespace-pre-wrap rounded-md border border-zinc-800 bg-zinc-950 p-3 font-mono text-sm leading-relaxed text-zinc-300">
              {run.input_text}
            </p>
          </section>

          <section className="relative ml-3 space-y-6 border-l border-zinc-800 pl-6">
            <div className="relative">
              <span className="absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full border border-teal-500/50 bg-teal-500/25 text-teal-400">
                <Play size={12} weight="fill" />
              </span>
              <div className="pl-2">
                <h3 className="text-sm font-semibold text-zinc-200">Workflow Started</h3>
                <p className="text-xs text-zinc-500">Input was normalized and analyzed.</p>
              </div>
            </div>

            {toolCalls && toolCalls.length > 0 ? (
              toolCalls.map((call) => {
                const isOpen = expandedCalls.has(call.id);
                return (
                  <ToolCallNode
                    key={call.id}
                    call={call}
                    isOpen={isOpen}
                    onToggle={() => toggleExpand(call.id)}
                  />
                );
              })
            ) : (
              !isTerminal && (
                <div className="relative">
                  <span className="absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full border border-zinc-700 bg-zinc-800 text-zinc-500">
                    <CircleNotch size={12} className="animate-spin" />
                  </span>
                  <div className="pl-2">
                    <h3 className="text-sm font-semibold text-zinc-400">
                      Agent planning next action...
                    </h3>
                  </div>
                </div>
              )
            )}

            {run.status === "waiting_for_approval" && (
              <div className="relative">
                <span className="absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full border border-amber-500/50 bg-amber-500/20 text-amber-400">
                  <Hourglass size={12} weight="fill" />
                </span>
                <div className="pl-2">
                  <h3 className="text-sm font-semibold text-amber-400">
                    Human Approval Gate
                  </h3>
                  <p className="text-xs text-zinc-500">
                    Sensitive action is paused until a reviewer approves and executes it.
                  </p>
                </div>
              </div>
            )}

            {isTerminal && (
              <div className="relative">
                <span
                  className={`absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full border ${
                    run.status === "completed"
                      ? "border-emerald-500/50 bg-emerald-500/25 text-emerald-400"
                      : run.status === "failed"
                        ? "border-red-500/50 bg-red-500/25 text-red-400"
                        : "border-zinc-700 bg-zinc-800 text-zinc-400"
                  }`}
                >
                  {run.status === "completed" ? (
                    <CheckCircle size={14} weight="fill" />
                  ) : run.status === "failed" ? (
                    <XCircle size={14} weight="fill" />
                  ) : (
                    <Prohibit size={14} weight="fill" />
                  )}
                </span>
                <div className="pl-2">
                  <h3 className="text-sm font-semibold text-zinc-200">
                    Execution Finished: {run.status}
                  </h3>
                  {run.error_message && (
                    <p className="mt-1 font-mono text-xs text-red-400">{run.error_message}</p>
                  )}
                </div>
              </div>
            )}
          </section>
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Run Meta
            </h3>
            <dl className="space-y-2 text-sm">
              <MetaRow label="Mode" value={run.mode.replace(/_/g, " ")} />
              <MetaRow label="Status" value={run.status.replace(/_/g, " ")} />
              {run.intent && <MetaRow label="Intent" value={run.intent.replace(/_/g, " ")} />}
              {run.priority && <MetaRow label="Priority" value={run.priority} />}
              {actions.length > 0 && <MetaRow label="Actions" value={String(actions.length)} />}
            </dl>
          </div>

          {draftResponse && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Draft Response
              </h3>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-300">
                {draftResponse}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricStrip({ counts }: { counts?: Record<string, number> }) {
  if (!counts) return null;

  const items = [
    ["Tool calls", counts.tool_calls],
    ["Pending approvals", counts.pending_approvals],
    ["Deliveries", counts.deliveries],
    ["Failed actions", counts.failed_actions],
  ].filter(([, value]) => typeof value === "number");

  if (!items.length) return null;

  return (
    <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-md border border-zinc-800 bg-zinc-950 px-3 py-2">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
            {label}
          </p>
          <p className="mt-1 font-mono text-lg font-semibold text-zinc-100">{value}</p>
        </div>
      ))}
    </div>
  );
}

function DeliveryPanel({ delivery }: { delivery: RunActionSummary }) {
  const isEmail = delivery.kind === "email";

  return (
    <article className="rounded-lg border border-emerald-500/25 bg-emerald-500/5 p-4">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
          {isEmail ? <EnvelopeSimple size={18} weight="bold" /> : <CheckCircle size={18} />}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-zinc-100">
              {delivery.label ?? readableToolName(delivery.tool_name)}
            </h3>
            <span className="rounded-md border border-emerald-500/25 bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-300">
              {delivery.delivery_status ?? delivery.status ?? "completed"}
            </span>
          </div>
          {isEmail ? (
            <div className="mt-3 space-y-2 text-sm">
              <KeyValue label="To" value={delivery.to} />
              <KeyValue label="Subject" value={delivery.subject} />
              {delivery.body && (
                <div>
                  <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                    Body
                  </p>
                  <p className="whitespace-pre-wrap rounded-md border border-zinc-800 bg-zinc-950 p-3 text-zinc-300">
                    {delivery.body}
                  </p>
                </div>
              )}
              <div className="grid gap-2 sm:grid-cols-2">
                <KeyValue label="Provider" value={delivery.provider} />
                <KeyValue label="Message ID" value={delivery.provider_message_id} mono />
              </div>
            </div>
          ) : (
            <p className="mt-2 text-sm text-zinc-400">{delivery.summary ?? delivery.download_url}</p>
          )}
        </div>
      </div>
    </article>
  );
}

function ApprovalLine({ approval }: { approval: RunApprovalSummary }) {
  return (
    <p className="text-sm text-zinc-300">
      <span className="font-medium text-amber-300">
        {readableToolName(approval.tool_name)}
      </span>{" "}
      is {approval.status.replace(/_/g, " ")}
      {approval.reviewer ? ` by ${approval.reviewer}` : ""}.
    </p>
  );
}

function ToolCallNode({
  call,
  isOpen,
  onToggle,
}: {
  call: ToolCall;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const output = call.output_payload ?? {};
  const input = call.input_payload ?? {};

  return (
    <div className="relative">
      <span
        className={`absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full border ${
          call.status === "completed"
            ? "border-emerald-500/50 bg-emerald-500/20 text-emerald-400"
            : call.status === "failed"
              ? "border-red-500/50 bg-red-500/20 text-red-400"
              : "border-amber-500/50 bg-amber-500/20 text-amber-400"
        }`}
      >
        <Hammer size={12} weight="bold" />
      </span>
      <div className="rounded-lg border border-zinc-800/80 bg-zinc-900/30 p-4 pl-4 transition-colors hover:border-zinc-700">
        <button
          onClick={onToggle}
          className="flex w-full items-center justify-between gap-4 text-left"
        >
          <div className="min-w-0">
            <h4 className="text-sm font-medium text-zinc-200">
              {readableToolName(call.tool_name)}
            </h4>
            <ToolCallPreview call={call} />
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <span
              className={`text-xs ${
                call.status === "completed"
                  ? "text-emerald-400"
                  : call.status === "failed"
                    ? "text-red-400"
                    : "text-amber-400"
              }`}
            >
              {call.status.replace(/_/g, " ")}
            </span>
            <span className="font-mono text-xs text-zinc-500">
              {isOpen ? "Collapse" : "Expand"}
            </span>
          </div>
        </button>

        {isOpen && (
          <div className="mt-4 space-y-3 border-t border-zinc-800 pt-3">
            <JsonBlock label="Input Payload" value={input} />
            {call.output_payload && <JsonBlock label="Output Payload" value={output} />}
            {call.error_message && (
              <div className="rounded-md border border-red-500/10 bg-red-500/5 p-3">
                <span className="mb-1 block text-xs font-semibold text-red-400">Error</span>
                <p className="font-mono text-xs text-red-300">{call.error_message}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ToolCallPreview({ call }: { call: ToolCall }) {
  if (call.tool_name === "send_email") {
    const payload = { ...call.input_payload, ...call.output_payload };
    return (
      <p className="mt-1 truncate text-xs text-zinc-500">
        {String(payload.to ?? "No recipient")} · {String(payload.subject ?? "No subject")}
      </p>
    );
  }

  return (
    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
      <span
        className={`rounded-md border px-1.5 py-0.5 text-[10px] font-semibold ${
          call.sensitivity === "blocked"
            ? "border-red-500/20 bg-red-500/10 text-red-400"
            : call.sensitivity === "approval_required"
              ? "border-amber-500/20 bg-amber-500/10 text-amber-400"
              : "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
        }`}
      >
        {call.sensitivity ?? "safe"}
      </span>
      {call.completed_at && <span className="text-zinc-500">Completed</span>}
    </div>
  );
}

function KeyValue({
  label,
  value,
  mono = false,
}: {
  label: string;
  value?: string | null;
  mono?: boolean;
}) {
  return (
    <div>
      <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
        {label}
      </p>
      <p className={`truncate text-zinc-300 ${mono ? "font-mono text-xs" : "text-sm"}`}>
        {value || "Not available"}
      </p>
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-zinc-500">{label}</dt>
      <dd className="truncate text-right font-medium capitalize text-zinc-300">{value}</dd>
    </div>
  );
}

function JsonBlock({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <span className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
        {label}
      </span>
      <pre className="overflow-x-auto rounded border border-zinc-850 bg-zinc-950 p-2 font-mono text-xs text-zinc-400">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}

function readableToolName(toolName?: string) {
  return toolName ? toolName.replace(/_/g, " ") : "Action";
}
