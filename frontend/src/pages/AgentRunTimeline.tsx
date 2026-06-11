/** Agent Run Timeline page. */

import {
  ArrowLeft,
  CircleNotch,
  CheckCircle,
  XCircle,
  Hourglass,
  Hammer,
  Play,
  Prohibit,
} from "@phosphor-icons/react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { cancelAgentRun, fetchAgentRun, fetchToolCalls } from "../lib/api";
import { createAgentRunSocket } from "../lib/websocket";
import { StatusBadge } from "../components/ui/StatusBadge";
import { ErrorState, LoadingState } from "../components/ui/States";
import { TimeAgo } from "../components/ui/TimeAgo";
import type { ToolCall, AgentRun } from "../types/models";

interface AgentRunTimelineProps {
  runId: string;
  onBack: () => void;
}

export function AgentRunTimeline({ runId, onBack }: AgentRunTimelineProps) {
  const queryClient = useQueryClient();
  const [expandedCalls, setExpandedCalls] = useState<Set<string>>(new Set());

  const { data: run, isLoading: isLoadingRun, error: runError } = useQuery<AgentRun>({
    queryKey: ["agent-run", runId],
    queryFn: () => fetchAgentRun(runId),
  });

  const { data: toolCalls, isLoading: isLoadingCalls, error: callsError } = useQuery<ToolCall[]>({
    queryKey: ["tool-calls", runId],
    queryFn: () => fetchToolCalls(runId),
    enabled: !!run,
  });

  // Setup WebSocket connection for live updates
  useEffect(() => {
    const ws = createAgentRunSocket(runId);
    ws.connect();

    const unsubscribe = ws.subscribe(() => {
      // Any event related to this run should trigger a refetch of data
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

  const isTerminal =
    run.status === "completed" ||
    run.status === "failed" ||
    run.status === "cancelled";

  return (
    <div>
      {/* Header */}
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
            <h1 className="text-xl font-semibold text-zinc-100 flex items-center gap-2">
              Agent Execution Timeline
              <span className="text-sm font-normal text-zinc-500 font-mono">({run.id.slice(0, 8)})</span>
            </h1>
            <div className="mt-2 flex items-center gap-3">
              <span className="text-xs uppercase tracking-wider font-semibold text-zinc-500">
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
        {/* Main Content: Vertical Timeline */}
        <div className="space-y-6">
          {/* Input Panel */}
          <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="mb-3 text-sm font-semibold text-zinc-300">Run Input</h2>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-300 font-mono bg-zinc-950 p-3 rounded-md border border-zinc-800">
              {run.input_text}
            </p>
          </section>

          {/* Timeline Nodes */}
          <section className="relative pl-6 border-l border-zinc-800 space-y-6 ml-3">
            {/* Start Node */}
            <div className="relative">
              <span className="absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full bg-teal-500/25 border border-teal-500/50 text-teal-400">
                <Play size={12} weight="fill" />
              </span>
              <div className="pl-2">
                <h3 className="text-sm font-semibold text-zinc-200">Workflow Started</h3>
                <p className="text-xs text-zinc-500">Initial inputs validated and normalized</p>
              </div>
            </div>

            {/* Steps & Tool Calls */}
            {toolCalls && toolCalls.length > 0 ? (
              toolCalls.map((call: ToolCall) => {
                const isOpen = expandedCalls.has(call.id);
                return (
                  <div key={call.id} className="relative">
                    <span className={`absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full border ${
                      call.status === "completed"
                        ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-400"
                        : call.status === "failed"
                        ? "bg-red-500/20 border-red-500/50 text-red-400"
                        : "bg-amber-500/20 border-amber-500/50 text-amber-400 animate-pulse"
                    }`}>
                      <Hammer size={12} weight="bold" />
                    </span>
                    <div className="pl-2 rounded-lg border border-zinc-800/80 bg-zinc-900/30 p-4 hover:border-zinc-700 transition-colors">
                      <div className="flex items-center justify-between gap-4 cursor-pointer" onClick={() => toggleExpand(call.id)}>
                        <div>
                          <h4 className="text-sm font-medium text-zinc-200">
                            Tool Call: {call.tool_name.replace(/_/g, " ")}
                          </h4>
                          <div className="mt-1 flex items-center gap-2 text-xs">
                            <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-semibold border ${
                              call.sensitivity === "blocked"
                                ? "bg-red-500/10 border-red-500/20 text-red-400"
                                : call.sensitivity === "approval_required"
                                ? "bg-amber-500/10 border-amber-500/20 text-amber-400"
                                : "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                            }`}>
                              {call.sensitivity ?? "safe"}
                            </span>
                            {call.duration_ms && (
                              <span className="text-zinc-500 font-mono">{call.duration_ms}ms</span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`text-xs ${
                            call.status === "completed"
                              ? "text-emerald-400"
                              : call.status === "failed"
                              ? "text-red-400"
                              : "text-amber-400"
                          }`}>
                            {call.status}
                          </span>
                          <span className="text-xs text-zinc-500 font-mono">
                            {isOpen ? "Collapse" : "Expand"}
                          </span>
                        </div>
                      </div>

                      {isOpen && (
                        <div className="mt-4 pt-3 border-t border-zinc-800 space-y-3">
                          <div>
                            <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 block mb-1">
                              Input Payload
                            </span>
                            <pre className="font-mono text-xs text-zinc-400 bg-zinc-950 p-2 rounded border border-zinc-850 overflow-x-auto">
                              {JSON.stringify(call.input_payload, null, 2)}
                            </pre>
                          </div>
                          {call.output_payload && (
                            <div>
                              <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 block mb-1">
                                Output Payload
                              </span>
                              <pre className="font-mono text-xs text-zinc-400 bg-zinc-950 p-2 rounded border border-zinc-850 overflow-x-auto">
                                {JSON.stringify(call.output_payload, null, 2)}
                              </pre>
                            </div>
                          )}
                          {call.error_message && (
                            <div className="rounded-md border border-red-500/10 bg-red-500/5 p-3">
                              <span className="text-xs font-semibold text-red-400 block mb-1">
                                Error
                              </span>
                              <p className="text-xs text-red-300 font-mono">{call.error_message}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              !isTerminal && (
                <div className="relative">
                  <span className="absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full bg-zinc-800 border border-zinc-700 text-zinc-500">
                    <CircleNotch size={12} className="animate-spin" />
                  </span>
                  <div className="pl-2">
                    <h3 className="text-sm font-semibold text-zinc-400">Agent planning next action...</h3>
                  </div>
                </div>
              )
            )}

            {/* Waiting for approval */}
            {run.status === "waiting_for_approval" && (
              <div className="relative animate-pulse">
                <span className="absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full bg-amber-500/20 border border-amber-500/50 text-amber-400">
                  <Hourglass size={12} weight="fill" />
                </span>
                <div className="pl-2">
                  <h3 className="text-sm font-semibold text-amber-400">Waiting for Human Approval</h3>
                  <p className="text-xs text-zinc-500">
                    A sensitive action requires explicit human review in the approvals queue.
                  </p>
                </div>
              </div>
            )}

            {/* End Node */}
            {isTerminal && (
              <div className="relative">
                <span className={`absolute -left-[31px] top-0 flex h-6 w-6 items-center justify-center rounded-full border ${
                  run.status === "completed"
                    ? "bg-emerald-500/25 border-emerald-500/50 text-emerald-400"
                    : run.status === "failed"
                    ? "bg-red-500/25 border-red-500/50 text-red-400"
                    : "bg-zinc-800 border-zinc-700 text-zinc-400"
                }`}>
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
                    <p className="mt-1 text-xs text-red-400 font-mono">{run.error_message}</p>
                  )}
                </div>
              </div>
            )}
          </section>
        </div>

        {/* Sidebar details */}
        <div className="space-y-4">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Run Meta
            </h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-zinc-500">Mode</dt>
                <dd className="font-mono text-zinc-300 capitalize">{run.mode.replace(/_/g, " ")}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-zinc-500">Status</dt>
                <dd className="font-mono text-zinc-300 capitalize">{run.status}</dd>
              </div>
              {run.intent && (
                <div className="flex justify-between">
                  <dt className="text-zinc-500">Intent</dt>
                  <dd className="text-zinc-200 font-semibold">{run.intent}</dd>
                </div>
              )}
              {run.priority && (
                <div className="flex justify-between">
                  <dt className="text-zinc-500">Priority</dt>
                  <dd className="text-zinc-200 font-semibold capitalize">{run.priority}</dd>
                </div>
              )}
            </dl>
          </div>

          {run.draft_response && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Draft Response
              </h3>
              <p className="text-sm text-zinc-300 whitespace-pre-wrap font-sans leading-relaxed">
                {run.draft_response}
              </p>
            </div>
          )}

          {run.final_output && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Final Output
              </h3>
              <p className="text-sm text-zinc-300 whitespace-pre-wrap font-mono leading-relaxed bg-zinc-950 p-2 rounded border border-zinc-850">
                {run.final_output}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
