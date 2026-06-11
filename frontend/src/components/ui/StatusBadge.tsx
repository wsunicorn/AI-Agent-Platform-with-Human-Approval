/** Shared UI: Status badges for various entity states. */

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

const STATUS_STYLES: Record<string, string> = {
  // Ticket statuses
  new: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  triaged: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
  in_progress: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  waiting_for_approval: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  resolved: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  closed: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",

  // Agent run statuses
  queued: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
  running: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  completed: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  failed: "bg-red-500/15 text-red-400 border-red-500/30",
  cancelled: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",

  // Approval statuses
  proposed: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
  pending_review: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  approved: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  rejected: "bg-red-500/15 text-red-400 border-red-500/30",
  edited: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
  executed: "bg-teal-500/15 text-teal-400 border-teal-500/30",

  // Sensitivity
  safe: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  approval_required: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  blocked: "bg-red-500/15 text-red-400 border-red-500/30",

  // Priorities
  low: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
  normal: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  urgent: "bg-red-500/15 text-red-400 border-red-500/30",
};

export function StatusBadge({ status, size = "sm" }: StatusBadgeProps) {
  const style = STATUS_STYLES[status] ?? "bg-zinc-500/15 text-zinc-400 border-zinc-500/30";
  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";

  return (
    <span
      className={`inline-flex items-center rounded-md border font-medium ${style} ${sizeClasses}`}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

/** Priority badge with dot indicator */
interface PriorityBadgeProps {
  priority: string;
}

const PRIORITY_DOTS: Record<string, string> = {
  urgent: "bg-red-400",
  high: "bg-orange-400",
  normal: "bg-blue-400",
  low: "bg-zinc-500",
};

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  const dotColor = PRIORITY_DOTS[priority] ?? "bg-zinc-500";
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-zinc-300">
      <span className={`inline-block h-2 w-2 rounded-full ${dotColor}`} />
      {priority}
    </span>
  );
}
