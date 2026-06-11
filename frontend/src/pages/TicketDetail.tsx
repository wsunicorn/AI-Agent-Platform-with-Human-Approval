/** Ticket Detail page. */

import { ArrowLeft, Lightning, Play } from "@phosphor-icons/react";
import { useQuery, useMutation } from "@tanstack/react-query";

import { createSupportRun, fetchTicket } from "../lib/api";
import { StatusBadge, PriorityBadge } from "../components/ui/StatusBadge";
import { ErrorState, LoadingState } from "../components/ui/States";
import { TimeAgo } from "../components/ui/TimeAgo";
import type { AgentRun, Ticket } from "../types/models";

interface TicketDetailProps {
  ticketId: string;
  onBack: () => void;
  onViewRun: (runId: string) => void;
}

export function TicketDetail({ ticketId, onBack, onViewRun }: TicketDetailProps) {
  const { data: ticket, isLoading, error } = useQuery({
    queryKey: ["ticket", ticketId],
    queryFn: () => fetchTicket(ticketId),
  });

  const runMutation = useMutation({
    mutationFn: () =>
      createSupportRun({
        input_text: ticket?.body ?? "",
        ticket_id: ticketId,
      }),
    onSuccess: (run: AgentRun) => {
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
            onClick={() => runMutation.mutate()}
            disabled={runMutation.isPending}
            className="flex items-center gap-2 rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-500 active:scale-[0.98] disabled:opacity-50"
          >
            <Play size={16} weight="fill" />
            {runMutation.isPending ? "Starting..." : "Run Agent"}
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
