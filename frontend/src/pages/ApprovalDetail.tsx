/** Approval Detail page. */

import { ArrowLeft, CheckCircle, XCircle, Pencil, Play } from "@phosphor-icons/react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
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

  // Initialize edited payload string when approval data is loaded
  useEffect(() => {
    if (approval) {
      const payload = approval.edited_payload || approval.proposed_payload;
      setEditedPayloadStr(JSON.stringify(payload, null, 2));
    }
  }, [approval]);

  const approveMut = useMutation({
    mutationFn: () => approveAction(approvalId, { reviewer: "admin" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approval", approvalId] });
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
  });

  const rejectMut = useMutation({
    mutationFn: () => rejectAction(approvalId, { reviewer: "admin" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approval", approvalId] });
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
  });

  const editMut = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editAction(approvalId, { reviewer: "admin", edited_payload: payload }),
    onSuccess: () => {
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ["approval", approvalId] });
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
  });

  const executeMut = useMutation({
    mutationFn: () => executeAction(approvalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["approval", approvalId] });
      queryClient.invalidateQueries({ queryKey: ["approvals"] });
    },
  });

  if (isLoading) return <LoadingState message="Loading approval request..." />;
  if (error || !approval) return <ErrorState message="Failed to load approval details" />;

  const handleSaveEdit = () => {
    try {
      const parsed = JSON.parse(editedPayloadStr);
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
                  onClick={() => setIsEditing(true)}
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
                      onClick={() => {
                        setIsEditing(false);
                        const payload = approval.edited_payload || approval.proposed_payload;
                        setEditedPayloadStr(JSON.stringify(payload, null, 2));
                      }}
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
                  {JSON.stringify(approval.edited_payload || approval.proposed_payload, null, 2)}
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
              {approval.reviewed_at && (
                <div className="flex justify-between">
                  <dt className="text-zinc-500">Reviewed At</dt>
                  <dd className="text-zinc-300"><TimeAgo date={approval.reviewed_at} /></dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}

// Simple key-value JSON diff helper
interface DiffLine {
  text: string;
  type: "add" | "remove" | "same";
}

function getPayloadDiff(
  original: Record<string, any>,
  edited: Record<string, any>
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
