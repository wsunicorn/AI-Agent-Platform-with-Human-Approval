/** Approval Detail page. */

import {
  ArrowLeft,
  CheckCircle,
  EnvelopeSimple,
  Pencil,
  Play,
  XCircle,
} from "@phosphor-icons/react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import CodeMirror from "@uiw/react-codemirror";

import {
  approveAction,
  executeAction,
  fetchApproval,
  rejectAction,
  editAction,
} from "../lib/api";
import { StatusBadge } from "../components/ui/StatusBadge";
import { ErrorState, LoadingState } from "../components/ui/States";
import { TimeAgo } from "../components/ui/TimeAgo";
import type { Approval } from "../types/models";

interface ApprovalDetailProps {
  approvalId: string;
  onBack: () => void;
}

export function ApprovalDetail({ approvalId, onBack }: ApprovalDetailProps) {
  const queryClient = useQueryClient();
  const [editedPayloadStr, setEditedPayloadStr] = useState<string>("");
  const [isEditing, setIsEditing] = useState(false);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const { data: approval, isLoading, error } = useQuery<Approval>({
    queryKey: ["approval", approvalId],
    queryFn: () => fetchApproval(approvalId),
  });

  const approveMut = useMutation({
    mutationFn: () => approveAction(approvalId, { reviewer: "admin" }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["approval", approvalId] });
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
      queryClient.invalidateQueries({ queryKey: ["agent-run", updated.agent_run_id] });
    },
  });

  const rejectMut = useMutation({
    mutationFn: () => rejectAction(approvalId, { reviewer: "admin" }),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["approval", approvalId] });
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
      queryClient.invalidateQueries({ queryKey: ["agent-run", updated.agent_run_id] });
    },
  });

  const editMut = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editAction(approvalId, { reviewer: "admin", edited_payload: payload }),
    onSuccess: (updated) => {
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ["approval", approvalId] });
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
      queryClient.invalidateQueries({ queryKey: ["agent-run", updated.agent_run_id] });
    },
  });

  const executeMut = useMutation({
    mutationFn: () => executeAction(approvalId),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ["approval", approvalId] });
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
      queryClient.invalidateQueries({ queryKey: ["agent-run", updated.agent_run_id] });
    },
  });

  if (isLoading) return <LoadingState message="Loading approval request..." />;
  if (error || !approval) return <ErrorState message="Failed to load approval details" />;

  const currentPayload = approval.edited_payload || approval.proposed_payload;
  const currentPayloadStr = JSON.stringify(currentPayload, null, 2);

  const handleStartEditing = () => {
    setEditedPayloadStr(currentPayloadStr);
    setJsonError(null);
    setIsEditing(true);
  };

  const handleCancelEditing = () => {
    setIsEditing(false);
    setJsonError(null);
    setEditedPayloadStr(currentPayloadStr);
  };

  const handleSaveEdit = () => {
    try {
      const parsed = JSON.parse(editedPayloadStr) as Record<string, unknown>;
      setJsonError(null);
      editMut.mutate(parsed);
    } catch (err) {
      setJsonError(err instanceof Error ? err.message : "Invalid JSON format");
    }
  };

  const isPending =
    approval.status === "pending_review" || approval.status === "proposed";

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={onBack}
          className="mb-4 flex items-center gap-1.5 text-sm text-zinc-500 transition-colors hover:text-zinc-300"
        >
          <ArrowLeft size={14} />
          Back to Queue
        </button>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-zinc-100 flex items-center gap-2">
              Review Action: {approval.tool_name.replace(/_/g, " ")}
            </h1>
            <div className="mt-2 flex items-center gap-3">
              <StatusBadge status={approval.status} />
              <span className="text-xs text-zinc-500 font-mono">
                Run ID: {approval.agent_run_id.slice(0, 8)}
              </span>
              <TimeAgo date={approval.created_at} />
            </div>
          </div>

          <div className="flex gap-2">
            {isPending && !isEditing && (
              <>
                <button
                  onClick={() => approveMut.mutate()}
                  disabled={approveMut.isPending}
                  className="flex items-center gap-1.5 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
                >
                  <CheckCircle size={16} weight="bold" />
                  Approve
                </button>
                <button
                  onClick={handleStartEditing}
                  className="flex items-center gap-1.5 rounded-md bg-zinc-850 border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800"
                >
                  <Pencil size={16} />
                  Edit Payload
                </button>
                <button
                  onClick={() => rejectMut.mutate()}
                  disabled={rejectMut.isPending}
                  className="flex items-center gap-1.5 rounded-md bg-red-650 px-4 py-2 text-sm font-medium text-white hover:bg-red-600"
                >
                  <XCircle size={16} weight="bold" />
                  Reject
                </button>
              </>
            )}

            {(approval.status === "approved" || approval.status === "edited") && (
              <button
                onClick={() => executeMut.mutate()}
                disabled={executeMut.isPending}
                className="flex items-center gap-1.5 rounded-md bg-teal-650 px-4 py-2 text-sm font-medium text-white hover:bg-teal-600"
              >
                <Play size={16} weight="fill" />
                Execute Action
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        {/* Main Content */}
        <div className="space-y-6">
          {/* Risk/Reason Panel */}
          {approval.risk_reason && (
            <div className="rounded-lg border border-amber-500/25 bg-amber-500/5 p-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-400">
                Risk Alert / Policy Reason
              </h3>
              <p className="mt-2 text-sm text-amber-300/90 leading-relaxed">
                {approval.risk_reason}
              </p>
            </div>
          )}

          {approval.tool_name === "send_email" && (
            <EmailApprovalPreview payload={currentPayload} status={approval.status} />
          )}

          {/* Payloads & Diff View */}
          <div className="grid gap-6 md:grid-cols-2">
            {/* Proposed Payload */}
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-5">
              <h2 className="mb-3 text-sm font-semibold text-zinc-300">
                Proposed Payload (Original)
              </h2>
              <pre className="font-mono text-xs text-zinc-400 bg-zinc-950 p-3 rounded-md border border-zinc-850 overflow-x-auto max-h-96">
                {JSON.stringify(approval.proposed_payload, null, 2)}
              </pre>
            </div>

            {/* Edited / Current Payload */}
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-5">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-zinc-300">
                  {isEditing ? "Editing Payload" : "Current Payload"}
                </h2>
                {isEditing && (
                  <div className="flex gap-2">
                    <button
                      onClick={handleSaveEdit}
                      disabled={editMut.isPending}
                      className="rounded bg-teal-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-teal-500"
                    >
                      Save
                    </button>
                    <button
                      onClick={handleCancelEditing}
                      className="rounded bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-300 hover:bg-zinc-700"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>

              {isEditing ? (
                <div className="space-y-2">
                  <div className="border border-zinc-750 rounded-md overflow-hidden bg-zinc-950">
                    <CodeMirror
                      value={editedPayloadStr}
                      onChange={(value) => setEditedPayloadStr(value)}
                      theme="dark"
                      basicSetup={{ lineNumbers: true, foldGutter: false }}
                    />
                  </div>
                  {jsonError && (
                    <p className="text-xs text-red-400 font-mono mt-1">{jsonError}</p>
                  )}
                </div>
              ) : (
                <pre className="font-mono text-xs text-zinc-400 bg-zinc-950 p-3 rounded-md border border-zinc-850 overflow-x-auto max-h-96">
                  {currentPayloadStr}
                </pre>
              )}
            </div>
          </div>

          {/* Simple Payload Diff View if edited */}
          {approval.edited_payload && (
            <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-5">
              <h2 className="mb-3 text-sm font-semibold text-zinc-300">Visual Diff</h2>
              <div className="font-mono text-xs space-y-1 bg-zinc-950 p-3 rounded-md border border-zinc-850 overflow-x-auto">
                {getPayloadDiff(approval.proposed_payload, approval.edited_payload).map((line, i) => (
                  <div
                    key={i}
                    className={`px-1.5 py-0.5 rounded ${
                      line.type === "add"
                        ? "bg-emerald-500/10 text-emerald-400"
                        : line.type === "remove"
                        ? "bg-red-500/10 text-red-400"
                        : "text-zinc-500"
                    }`}
                  >
                    {line.text}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Sidebar Info */}
        <div className="space-y-4">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Audit Info
            </h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-zinc-500">Reviewer</dt>
                <dd className="font-medium text-zinc-300">{approval.reviewer || "Not reviewed"}</dd>
              </div>
              {approval.reviewer_comment && (
                <div>
                  <dt className="text-zinc-500">Reviewer Note</dt>
                  <dd className="mt-1 text-zinc-300">{approval.reviewer_comment}</dd>
                </div>
              )}
              {approval.reviewed_at && (
                <div className="flex justify-between">
                  <dt className="text-zinc-500">Reviewed At</dt>
                  <dd className="text-zinc-300"><TimeAgo date={approval.reviewed_at} /></dd>
                </div>
              )}
              {approval.executed_at && (
                <div className="flex justify-between">
                  <dt className="text-zinc-500">Executed At</dt>
                  <dd className="text-zinc-300"><TimeAgo date={approval.executed_at} /></dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}

function EmailApprovalPreview({
  payload,
  status,
}: {
  payload: Record<string, unknown>;
  status: string;
}) {
  const to = String(payload.to ?? "");
  const subject = String(payload.subject ?? "");
  const body = String(payload.body ?? "");

  return (
    <section className="rounded-lg border border-teal-500/25 bg-teal-500/5 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <EnvelopeSimple size={18} className="text-teal-300" weight="bold" />
          <h2 className="text-sm font-semibold text-zinc-100">Email Preview</h2>
        </div>
        <span className="rounded-md border border-teal-500/25 bg-teal-500/10 px-2 py-0.5 text-xs font-medium text-teal-300">
          {status.replace(/_/g, " ")}
        </span>
      </div>
      <div className="grid gap-3 text-sm md:grid-cols-2">
        <PreviewField label="To" value={to || "Missing recipient"} />
        <PreviewField label="Subject" value={subject || "Missing subject"} />
      </div>
      <div className="mt-3">
        <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
          Body
        </p>
        <p className="whitespace-pre-wrap rounded-md border border-zinc-800 bg-zinc-950 p-3 text-sm leading-relaxed text-zinc-300">
          {body || "Missing body"}
        </p>
      </div>
    </section>
  );
}

function PreviewField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
        {label}
      </p>
      <p className="truncate text-sm text-zinc-300">{value}</p>
    </div>
  );
}

// Simple key-value JSON diff helper
interface DiffLine {
  text: string;
  type: "add" | "remove" | "same";
}

function getPayloadDiff(
  original: Record<string, unknown>,
  edited: Record<string, unknown>,
): DiffLine[] {
  const lines: DiffLine[] = [];
  const allKeys = Array.from(new Set([...Object.keys(original), ...Object.keys(edited)]));

  for (const key of allKeys) {
    if (!(key in original)) {
      lines.push({ text: `+ ${key}: ${JSON.stringify(edited[key])}`, type: "add" });
    } else if (!(key in edited)) {
      lines.push({ text: `- ${key}: ${JSON.stringify(original[key])}`, type: "remove" });
    } else if (JSON.stringify(original[key]) !== JSON.stringify(edited[key])) {
      lines.push({ text: `- ${key}: ${JSON.stringify(original[key])}`, type: "remove" });
      lines.push({ text: `+ ${key}: ${JSON.stringify(edited[key])}`, type: "add" });
    } else {
      lines.push({ text: `  ${key}: ${JSON.stringify(original[key])}`, type: "same" });
    }
  }

  return lines;
}
