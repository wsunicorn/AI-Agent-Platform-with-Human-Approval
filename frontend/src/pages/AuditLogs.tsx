/** Audit Log Explorer page. */

import { ListChecks } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { fetchAuditLogs } from "../lib/api";
import { EmptyState, ErrorState, SkeletonRows } from "../components/ui/States";
import { TimeAgo } from "../components/ui/TimeAgo";
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
          Complete audit trail of all system actions
        </p>
      </div>

      {/* Filters */}
      <div className="mb-4 flex gap-2">
        {["", "ticket", "agent_run", "tool_call", "approval_request"].map(
          (t) => (
            <button
              key={t}
              onClick={() => setEntityFilter(t)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                entityFilter === t
                  ? "bg-zinc-700 text-zinc-100"
                  : "bg-zinc-900 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300"
              }`}
            >
              {t ? t.replace(/_/g, " ") : "All"}
            </button>
          )
        )}
      </div>

      {/* Log List */}
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
          {logs.map((log: AuditLog) => (
            <div key={log.id}>
              <button
                onClick={() => toggleExpand(log.id)}
                className="flex w-full items-center gap-3 rounded-md border border-zinc-800 bg-zinc-900/50 px-4 py-3 text-left transition-colors hover:border-zinc-700"
              >
                <ListChecks size={16} className="shrink-0 text-zinc-500" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-zinc-200">
                      {log.action}
                    </span>
                    {log.entity_type && (
                      <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs text-zinc-400">
                        {log.entity_type}
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {log.actor_type}
                    {log.actor_id ? ` · ${log.actor_id}` : ""}
                  </p>
                </div>
                <TimeAgo date={log.created_at} />
              </button>

              {/* Expanded Details */}
              {expanded.has(log.id) && (
                <div className="ml-7 mt-1 mb-2 rounded-md border border-zinc-800 bg-zinc-800/30 p-3 space-y-2">
                  {log.entity_id && (
                    <div className="text-xs">
                      <span className="text-zinc-500">Entity ID:</span>{" "}
                      <span className="font-mono text-zinc-400">{log.entity_id}</span>
                    </div>
                  )}
                  {log.before_state && (
                    <div>
                      <p className="mb-1 text-xs font-semibold text-zinc-500">Before:</p>
                      <pre className="font-mono text-xs text-zinc-400 max-h-24 overflow-auto">
                        {JSON.stringify(log.before_state, null, 2)}
                      </pre>
                    </div>
                  )}
                  {log.after_state && (
                    <div>
                      <p className="mb-1 text-xs font-semibold text-zinc-500">After:</p>
                      <pre className="font-mono text-xs text-zinc-400 max-h-24 overflow-auto">
                        {JSON.stringify(log.after_state, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
