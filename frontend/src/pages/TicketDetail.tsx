/** Ticket Detail page. */

import { ArrowLeft, ClockCounterClockwise, Lightning, Play } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createSupportRun, fetchAgentRuns, fetchTicket } from "../lib/api";
import { StatusBadge, PriorityBadge } from "../components/ui/StatusBadge";
import { ErrorState, LoadingState } from "../components/ui/States";
import { TimeAgo } from "../components/ui/TimeAgo";
import type { AgentRun } from "../types/models";

interface TicketDetailProps {
  ticketId: string;
  onBack: () => void;
  onViewRun: (runId: string) => void;
}

export function TicketDetail({ ticketId, onBack, onViewRun }: TicketDetailProps) {
  const queryClient = useQueryClient();
  const { data: ticket, isLoading, error } = useQuery({
    queryKey: ["ticket", ticketId],
    queryFn: () => fetchTicket(ticketId),
  });

  const { data: runs, isLoading: isLoadingRuns } = useQuery({
    queryKey: ["agent-runs", ticketId],
    queryFn: () => fetchAgentRuns({ ticket_id: ticketId, limit: 10 }),
    refetchInterval: 5000,
  });

  const latestRun = runs?.[0];
  const activeRun = runs?.find((run) =>
    ["queued", "running", "waiting_for_approval"].includes(run.status),
  );

  const runMutation = useMutation({
    mutationFn: () =>
      createSupportRun({
        input_text: ticket?.body ?? "",
        ticket_id: ticketId,
      }),
    onSuccess: (run: AgentRun) => {
      queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["agent-runs", ticketId] });
      onViewRun(run.id);
    },
  });

  if (isLoading) return <LoadingState message="Loading ticket..." />;
  if (error || !ticket) return <ErrorState message="Failed to load ticket" />;

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={onBack}
          className="mb-4 flex items-center gap-1.5 text-sm text-zinc-500 transition-colors hover:text-zinc-300"
        >
          <ArrowLeft size={14} />
          Back to Inbox
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-zinc-100">
              {ticket.subject}
            </h1>
            <div className="mt-2 flex items-center gap-3">
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
              <TimeAgo date={ticket.created_at} />
            </div>
          </div>
          <button
            onClick={() => {
              if (activeRun) onViewRun(activeRun.id);
              else runMutation.mutate();
            }}
            disabled={runMutation.isPending}
            className="flex items-center gap-2 rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-500 active:scale-[0.98] disabled:opacity-50"
          >
            <Play size={16} weight="fill" />
            {buttonLabel(runMutation.isPending, activeRun)}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {/* Main */}
        <div className="space-y-6">
          {/* Customer info */}
          <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="mb-3 text-sm font-semibold text-zinc-300">
              Customer
            </h2>
            <dl className="space-y-2 text-sm">
              {ticket.customer_name && (
                <div className="flex justify-between">
                  <dt className="text-zinc-500">Name</dt>
                  <dd className="text-zinc-200">{ticket.customer_name}</dd>
                </div>
              )}
              {ticket.customer_email && (
                <div className="flex justify-between">
                  <dt className="text-zinc-500">Email</dt>
                  <dd className="font-mono text-zinc-200">{ticket.customer_email}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-zinc-500">Channel</dt>
                <dd className="text-zinc-200">{ticket.channel}</dd>
              </div>
            </dl>
          </section>

          {/* Original Message */}
          <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="mb-3 text-sm font-semibold text-zinc-300">
              Original Message
            </h2>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-300">
              {ticket.body}
            </p>
          </section>

          <section className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="text-sm font-semibold text-zinc-300">Agent Runs</h2>
              {latestRun && (
                <button
                  onClick={() => onViewRun(latestRun.id)}
                  className="text-xs font-medium text-teal-300 hover:text-teal-200"
                >
                  View latest timeline
                </button>
              )}
            </div>
            {isLoadingRuns ? (
              <p className="text-sm text-zinc-500">Loading run history...</p>
            ) : !runs?.length ? (
              <p className="text-sm text-zinc-500">
                No agent run yet. Start one to draft and review the customer response.
              </p>
            ) : (
              <div className="space-y-2">
                {runs.map((run) => (
                  <button
                    key={run.id}
                    onClick={() => onViewRun(run.id)}
                    className="flex w-full items-center justify-between gap-3 rounded-md border border-zinc-800 bg-zinc-950/60 px-3 py-2 text-left transition-colors hover:border-zinc-700"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <ClockCounterClockwise size={14} className="text-zinc-500" />
                        <span className="font-mono text-xs text-zinc-400">
                          {run.id.slice(0, 8)}
                        </span>
                        <StatusBadge status={run.status} />
                      </div>
                      <p className="mt-1 truncate text-xs text-zinc-500">
                        {run.final_output?.summary ?? run.error_message ?? "Preparing run summary"}
                      </p>
                    </div>
                    <TimeAgo date={run.updated_at} />
                  </button>
                ))}
              </div>
            )}
          </section>
        </div>

        {/* Sidebar info */}
        <div className="space-y-4">
          {ticket.intent && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Intent
              </h3>
              <div className="flex items-center gap-2">
                <Lightning size={16} className="text-amber-400" />
                <span className="text-sm font-medium text-zinc-200">
                  {ticket.intent}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function buttonLabel(isStarting: boolean, activeRun?: AgentRun) {
  if (isStarting) return "Starting...";
  if (!activeRun) return "Run Agent";
  if (activeRun.status === "waiting_for_approval") return "Review Current Run";
  return "View Running Agent";
}
