/** Audit Log Explorer page. */

import { CheckCircle, Info, WarningCircle, XCircle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { EmptyState, ErrorState, SkeletonRows } from "../components/ui/States";
import { TimeAgo } from "../components/ui/TimeAgo";
import { fetchAuditLogs } from "../lib/api";
import type { AuditLog } from "../types/models";

export function AuditLogExplorer() {
  const [entityFilter, setEntityFilter] = useState<string>("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const { data: logs, isLoading, error, refetch } = useQuery({
    queryKey: ["audit-logs", entityFilter],
    queryFn: () =>
      fetchAuditLogs({
        entity_type: entityFilter || undefined,
        limit: 100,
      }),
    refetchInterval: 10000,
  });

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-zinc-100">Audit Logs</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Human-readable trail of reviews, tool calls, and delivery outcomes
        </p>
      </div>

      <div className="mb-4 flex gap-2">
        {["", "ticket", "agent_run", "tool_call", "approval_request"].map((type) => (
          <button
            key={type}
            onClick={() => setEntityFilter(type)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              entityFilter === type
                ? "bg-zinc-700 text-zinc-100"
                : "bg-zinc-900 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
            }`}
          >
            {type ? type.replace(/_/g, " ") : "All"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <SkeletonRows count={8} />
      ) : error ? (
        <ErrorState message={String(error)} onRetry={refetch} />
      ) : !logs?.length ? (
        <EmptyState
          title="No audit logs"
          description="Actions and events will be logged here automatically"
        />
      ) : (
        <div className="space-y-1">
          {logs.map((log) => (
            <div key={log.id}>
              <button
                onClick={() => toggleExpand(log.id)}
                className="flex w-full items-center gap-3 rounded-md border border-zinc-800 bg-zinc-900/50 px-4 py-3 text-left transition-colors hover:border-zinc-700"
              >
                <SeverityIcon severity={log.severity} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-zinc-200">
                      {log.message || log.action}
                    </span>
                    {log.entity_type && (
                      <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs text-zinc-400">
                        {log.entity_type}
                      </span>
                    )}
                    <span className={`rounded px-1.5 py-0.5 text-xs ${severityClass(log.severity)}`}>
                      {log.severity}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {log.actor_type}
                    {log.actor_id ? ` · ${log.actor_id}` : ""}
                    {log.message ? ` · ${log.action}` : ""}
                  </p>
                </div>
                <TimeAgo date={log.created_at} />
              </button>

              {expanded.has(log.id) && (
                <div className="mb-2 ml-7 mt-1 space-y-2 rounded-md border border-zinc-800 bg-zinc-800/30 p-3">
                  {log.entity_id && (
                    <div className="text-xs">
                      <span className="text-zinc-500">Entity ID:</span>{" "}
                      <span className="font-mono text-zinc-400">{log.entity_id}</span>
                    </div>
                  )}
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <JsonDetails label="Metadata" value={log.metadata} />
                  )}
                  {log.before_state && <JsonDetails label="Before" value={log.before_state} />}
                  {log.after_state && <JsonDetails label="After" value={log.after_state} />}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SeverityIcon({ severity }: { severity: AuditLog["severity"] }) {
  const className = `shrink-0 ${iconClass(severity)}`;
  if (severity === "success") return <CheckCircle size={16} className={className} weight="bold" />;
  if (severity === "warning") {
    return <WarningCircle size={16} className={className} weight="bold" />;
  }
  if (severity === "error") return <XCircle size={16} className={className} weight="bold" />;
  return <Info size={16} className={className} weight="bold" />;
}

function iconClass(severity: AuditLog["severity"]) {
  switch (severity) {
    case "success":
      return "text-emerald-400";
    case "warning":
      return "text-amber-400";
    case "error":
      return "text-red-400";
    default:
      return "text-zinc-500";
  }
}

function severityClass(severity: AuditLog["severity"]) {
  switch (severity) {
    case "success":
      return "bg-emerald-500/10 text-emerald-300";
    case "warning":
      return "bg-amber-500/10 text-amber-300";
    case "error":
      return "bg-red-500/10 text-red-300";
    default:
      return "bg-zinc-800 text-zinc-400";
  }
}

function JsonDetails({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <p className="mb-1 text-xs font-semibold text-zinc-500">{label}:</p>
      <pre className="max-h-28 overflow-auto font-mono text-xs text-zinc-400">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}
