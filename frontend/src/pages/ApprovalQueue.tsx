/** Approval Queue page. */

import { CheckCircle, EnvelopeSimple, Play, ShieldCheck, XCircle } from "@phosphor-icons/react";
import type { UseMutationResult } from "@tanstack/react-query";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  approveAction,
  executeAction,
  fetchApprovals,
  rejectAction,
} from "../lib/api";
import { StatusBadge } from "../components/ui/StatusBadge";
import { EmptyState, ErrorState, SkeletonRows } from "../components/ui/States";
import { TimeAgo } from "../components/ui/TimeAgo";
import type { Approval } from "../types/models";

interface ApprovalQueueProps {
  onSelectApproval: (id: string) => void;
}

export function ApprovalQueue({ onSelectApproval }: ApprovalQueueProps) {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const queryClient = useQueryClient();

  const { data: approvals, isLoading, error, refetch } = useQuery({
    queryKey: ["approvals", statusFilter],
    queryFn: () => fetchApprovals({ status: statusFilter || undefined }),
    refetchInterval: 5000,
  });

  const approveMut = useMutation({
    mutationFn: (id: string) => approveAction(id, { reviewer: "admin" }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
      queryClient.invalidateQueries({ queryKey: ["agent-run", updated.agent_run_id] });
    },
  });

  const rejectMut = useMutation({
    mutationFn: (id: string) => rejectAction(id, { reviewer: "admin" }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
      queryClient.invalidateQueries({ queryKey: ["agent-run", updated.agent_run_id] });
    },
  });

  const executeMut = useMutation({
    mutationFn: (id: string) => executeAction(id),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
      queryClient.invalidateQueries({ queryKey: ["agent-run", updated.agent_run_id] });
    },
  });

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-zinc-100">Approval Queue</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Review and approve agent-proposed actions
        </p>
      </div>

      {/* Filters */}
      <div className="mb-4 flex gap-2">
        {["", "pending_review", "approved", "rejected", "executed"].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              statusFilter === s
                ? "bg-zinc-700 text-zinc-100"
                : "bg-zinc-900 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
            }`}
          >
            {s ? s.replace(/_/g, " ") : "All"}
          </button>
        ))}
      </div>

      {/* Approval List */}
      {isLoading ? (
        <SkeletonRows count={4} />
      ) : error ? (
        <ErrorState message={String(error)} onRetry={refetch} />
      ) : !approvals?.length ? (
        <EmptyState
          title="No approvals"
          description="Agent-proposed actions requiring review will appear here"
        />
      ) : (
        <div className="space-y-2">
          {approvals.map((approval: Approval) => (
            <div
              key={approval.id}
              onClick={() => onSelectApproval(approval.id)}
              className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 hover:border-zinc-700 transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <ShieldCheck size={20} className="text-amber-400" />
                  <div>
                    <p className="text-sm font-medium text-zinc-200">
                      {approval.tool_name.replace(/_/g, " ")}
                    </p>
                    {approval.risk_reason && (
                      <p className="mt-0.5 text-xs text-zinc-500">
                      {approval.risk_reason}
                    </p>
                  )}
                    <p className="mt-1 text-xs text-zinc-500">
                      {statusHint(approval)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={approval.status} />
                  <TimeAgo date={approval.created_at} />
                </div>
              </div>

              <ApprovalPayloadPreview approval={approval} />

              <MutationErrorHint
                mutations={[approveMut, rejectMut, executeMut]}
                approvalId={approval.id}
              />

              {/* Actions */}
              {(approval.status === "pending_review" ||
                approval.status === "proposed") && (
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); approveMut.mutate(approval.id); }}
                    disabled={approveMut.isPending}
                    className="flex items-center gap-1.5 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-500"
                  >
                    <CheckCircle size={14} weight="bold" />
                    Approve
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); rejectMut.mutate(approval.id); }}
                    disabled={rejectMut.isPending}
                    className="flex items-center gap-1.5 rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-500"
                  >
                    <XCircle size={14} weight="bold" />
                    Reject
                  </button>
                </div>
              )}

              {(approval.status === "approved" || approval.status === "edited") && (
                <div className="mt-3">
                  <button
                    onClick={(e) => { e.stopPropagation(); executeMut.mutate(approval.id); }}
                    disabled={executeMut.isPending}
                    className="flex items-center gap-1.5 rounded-md bg-teal-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-teal-500"
                  >
                    <Play size={14} weight="fill" />
                    Execute
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MutationErrorHint({
  mutations,
  approvalId,
}: {
  mutations: UseMutationResult<Approval, Error, string>[];
  approvalId: string;
}) {
  const failed = mutations.find((m) => m.isError && m.variables === approvalId);
  if (!failed) return null;
  return (
    <p className="mt-2 rounded-md border border-red-900 bg-red-950/40 px-2.5 py-1.5 text-xs text-red-400">
      {failed.error instanceof Error ? failed.error.message : "Action failed."}
    </p>
  );
}

function ApprovalPayloadPreview({ approval }: { approval: Approval }) {
  const payload = approval.edited_payload ?? approval.proposed_payload;

  if (approval.tool_name === "send_email") {
    return (
      <div className="mt-3 rounded-md border border-teal-500/20 bg-teal-500/5 p-3">
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-teal-300">
          <EnvelopeSimple size={14} weight="bold" />
          Email Preview
        </div>
        <div className="grid gap-2 text-xs md:grid-cols-2">
          <PreviewField label="To" value={payload.to} />
          <PreviewField label="Subject" value={payload.subject} />
        </div>
        <p className="mt-2 line-clamp-3 whitespace-pre-wrap text-xs leading-relaxed text-zinc-400">
          {String(payload.body ?? "No body")}
        </p>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-md bg-zinc-800/50 p-3">
      <pre className="max-h-32 overflow-y-auto overflow-x-auto font-mono text-xs text-zinc-400">
        {JSON.stringify(payload, null, 2)}
      </pre>
    </div>
  );
}

function PreviewField({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <span className="text-zinc-500">{label}</span>
      <p className="truncate font-medium text-zinc-300">{String(value ?? "Missing")}</p>
    </div>
  );
}

function statusHint(approval: Approval) {
  switch (approval.status) {
    case "pending_review":
    case "proposed":
      return "Needs a human decision before anything is sent or written.";
    case "approved":
    case "edited":
      return "Approved, but not executed yet.";
    case "executed":
      return "Executed. Check the agent run timeline for delivery details.";
    case "rejected":
      return "Rejected. The sensitive action was not executed.";
    case "failed":
      return "Execution failed. Review the detail page for the error.";
    default:
      return "No action needed right now.";
  }
}
