/** Empty, loading, and error state components. */

import { CircleNotch, SmileySad, Tray } from "@phosphor-icons/react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <Tray size={48} weight="thin" className="mb-4 text-zinc-600" />
      <h3 className="text-base font-semibold text-zinc-300">{title}</h3>
      {description && (
        <p className="mt-1.5 max-w-sm text-sm text-zinc-500">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <CircleNotch
        size={32}
        weight="bold"
        className="mb-3 animate-spin text-teal-400"
      />
      <p className="text-sm text-zinc-400">{message}</p>
    </div>
  );
}

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <SmileySad size={48} weight="thin" className="mb-4 text-red-400/60" />
      <h3 className="text-base font-semibold text-zinc-300">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-zinc-500">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 rounded-md bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-200 transition-colors hover:bg-zinc-700 active:scale-[0.98]"
        >
          Try again
        </button>
      )}
    </div>
  );
}

/** Skeleton loader rows. */
export function SkeletonRows({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="h-14 animate-pulse rounded-md bg-zinc-800/50"
          style={{ animationDelay: `${i * 80}ms` }}
        />
      ))}
    </div>
  );
}
