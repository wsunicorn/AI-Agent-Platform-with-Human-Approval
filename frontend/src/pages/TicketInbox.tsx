/** Ticket Inbox page. */

import { Envelope, MagnifyingGlass, Plus } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { createTicket, fetchTickets } from "../lib/api";
import { StatusBadge, PriorityBadge } from "../components/ui/StatusBadge";
import { EmptyState, ErrorState, SkeletonRows } from "../components/ui/States";
import { TimeAgo } from "../components/ui/TimeAgo";
import type { Ticket } from "../types/models";

interface TicketInboxProps {
  onSelectTicket: (id: string) => void;
}

export function TicketInbox({ onSelectTicket }: TicketInboxProps) {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [showCreate, setShowCreate] = useState(false);

  const { data: tickets, isLoading, error, refetch } = useQuery({
    queryKey: ["tickets", statusFilter],
    queryFn: () => fetchTickets({ status: statusFilter || undefined }),
    refetchInterval: 10000,
  });

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-zinc-100">Ticket Inbox</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Support tickets and agent processing status
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-teal-500 active:scale-[0.98]"
        >
          <Plus size={16} weight="bold" />
          New Ticket
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <CreateTicketForm
          onCreated={() => {
            setShowCreate(false);
            refetch();
          }}
          onCancel={() => setShowCreate(false)}
        />
      )}

      {/* Filters */}
      <div className="mb-4 flex gap-2">
        {["", "new", "in_progress", "waiting_for_approval", "resolved"].map(
          (s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                statusFilter === s
                  ? "bg-zinc-700 text-zinc-100"
                  : "bg-zinc-900 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
              }`}
            >
              {s || "All"}
            </button>
          )
        )}
      </div>

      {/* Ticket List */}
      {isLoading ? (
        <SkeletonRows count={6} />
      ) : error ? (
        <ErrorState message={String(error)} onRetry={refetch} />
      ) : !tickets?.length ? (
        <EmptyState
          title="No tickets found"
          description="Create a ticket to get started with AI-powered support"
        />
      ) : (
        <div className="space-y-1">
          {tickets.map((ticket: Ticket) => (
            <button
              key={ticket.id}
              onClick={() => onSelectTicket(ticket.id)}
              className="flex w-full items-center gap-4 rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3 text-left transition-colors hover:border-zinc-700 hover:bg-zinc-900"
            >
              <Envelope size={18} className="shrink-0 text-zinc-500" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-zinc-200">
                  {ticket.subject}
                </p>
                <p className="mt-0.5 truncate text-xs text-zinc-500">
                  {ticket.customer_name || ticket.customer_email || "Unknown"}
                </p>
              </div>
              <PriorityBadge priority={ticket.priority} />
              <StatusBadge status={ticket.status} />
              <TimeAgo date={ticket.created_at} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/** Inline create ticket form */
function CreateTicketForm({
  onCreated,
  onCancel,
}: {
  onCreated: () => void;
  onCancel: () => void;
}) {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await createTicket({
        subject,
        body,
        customer_email: email || undefined,
      });
      onCreated();
    } catch (err: any) {
      setError(err?.message || "Failed to create ticket");
    } finally {
      setLoading(false);
    }
  };


  return (
    <form
      onSubmit={handleSubmit}
      className="mb-6 rounded-lg border border-zinc-800 bg-zinc-900/70 p-5"
    >
      {error && (
        <div className="mb-4 rounded-md border border-red-900 bg-red-950/40 p-3 text-xs text-red-400">
          {error}
        </div>
      )}
      <div className="space-y-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">
            Subject
          </label>
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Brief summary of the issue"
            required
            className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-teal-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">
            Message
          </label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Describe the issue in detail"
            required
            rows={4}
            className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-teal-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">
            Customer Email
          </label>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            placeholder="customer@example.com"
            className="w-full rounded-md border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-600 focus:border-teal-500 focus:outline-none"
          />
        </div>
      </div>
      <div className="mt-4 flex gap-2">
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500 disabled:opacity-50"
        >
          {loading ? "Creating..." : "Create Ticket"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-700"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
