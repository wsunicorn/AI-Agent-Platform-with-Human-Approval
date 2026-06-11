/** Relative time display. */

import { timeAgo } from "./relativeTime";

export function TimeAgo({ date }: { date: string }) {
  return (
    <time
      dateTime={date}
      title={new Date(date).toLocaleString()}
      className="text-xs text-zinc-500 tabular-nums"
    >
      {timeAgo(date)}
    </time>
  );
}
