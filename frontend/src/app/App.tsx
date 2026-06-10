import { useEffect, useState } from "react";

import { getApiHealth } from "../lib/api";

type HealthState = {
  live: string;
  ready: string;
  detail?: string;
};

export function App() {
  const [health, setHealth] = useState<HealthState>({
    live: "checking",
    ready: "checking",
  });

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      try {
        const result = await getApiHealth();
        if (!cancelled) {
          setHealth(result);
        }
      } catch (error) {
        if (!cancelled) {
          setHealth({
            live: "failed",
            ready: "failed",
            detail: error instanceof Error ? error.message : "Unknown error",
          });
        }
      }
    }

    void loadHealth();
    const timer = window.setInterval(loadHealth, 10000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <main className="min-h-[100dvh] bg-zinc-50 text-zinc-950">
      <section className="mx-auto flex min-h-[100dvh] w-full max-w-6xl flex-col justify-center px-6 py-10">
        <div className="grid gap-8 lg:grid-cols-[1fr_360px] lg:items-center">
          <div>
            <p className="text-sm font-medium text-teal-700">HumanGate AI</p>
            <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight tracking-normal md:text-6xl">
              AI support operations with human approval.
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-zinc-600">
              The project shell is ready for FastAPI, LangGraph, PostgreSQL, Redis,
              Gemini, Ollama, and the React approval dashboard.
            </p>
          </div>

          <div className="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-zinc-200 pb-4">
              <div>
                <h2 className="text-base font-semibold">System status</h2>
                <p className="mt-1 text-sm text-zinc-500">Auto-refreshes every 10 seconds</p>
              </div>
              <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700">
                Phase 2
              </span>
            </div>

            <dl className="mt-5 space-y-3">
              <StatusRow label="API live" value={health.live} />
              <StatusRow label="API ready" value={health.ready} />
            </dl>

            {health.detail ? (
              <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{health.detail}</p>
            ) : null}
          </div>
        </div>
      </section>
    </main>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  const isOk = value === "ok";

  return (
    <div className="flex items-center justify-between rounded-md border border-zinc-200 px-3 py-2">
      <dt className="text-sm text-zinc-600">{label}</dt>
      <dd
        className={
          isOk
            ? "text-sm font-semibold text-teal-700"
            : "text-sm font-semibold text-amber-700"
        }
      >
        {value}
      </dd>
    </div>
  );
}

