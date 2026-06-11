/** Top status bar component. */

import { Circle, Plugs, WifiHigh, WifiSlash } from "@phosphor-icons/react";
import { useEffect, useState } from "react";

import { getHealth } from "../../lib/api";

export function TopBar() {
  const [health, setHealth] = useState<{
    live: string;
    ready: string;
  }>({ live: "checking", ready: "checking" });

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const result = await getHealth();
        if (!cancelled) setHealth({ live: result.live, ready: result.ready });
      } catch {
        if (!cancelled) setHealth({ live: "failed", ready: "failed" });
      }
    };
    check();
    const timer = setInterval(check, 15000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const isHealthy = health.live === "ok" && health.ready === "ok";

  return (
    <header className="dashboard-topbar flex items-center justify-between border-b border-zinc-800 bg-zinc-950 px-6">
      <div className="flex items-center gap-2 text-sm text-zinc-400">
        <Plugs size={16} weight="bold" />
        <span>Support Operations</span>
      </div>

      <div className="flex items-center gap-4">
        {/* System Status */}
        <div className="flex items-center gap-2">
          {isHealthy ? (
            <WifiHigh size={16} className="text-emerald-400" />
          ) : (
            <WifiSlash size={16} className="text-red-400" />
          )}
          <div className="flex items-center gap-1.5">
            <Circle
              size={8}
              weight="fill"
              className={isHealthy ? "text-emerald-400" : "text-red-400"}
            />
            <span className="text-xs text-zinc-400">
              {isHealthy ? "Connected" : "Disconnected"}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
