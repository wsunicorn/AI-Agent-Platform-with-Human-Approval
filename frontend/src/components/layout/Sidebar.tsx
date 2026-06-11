/** Sidebar navigation component. */

import {
  Database,
  Envelope,
  Gear,
  ListChecks,
  ShieldCheck,
  Stack,
} from "@phosphor-icons/react";

const NAV_ITEMS = [
  { label: "Tickets", icon: Envelope, path: "/tickets" },
  { label: "Approvals", icon: ShieldCheck, path: "/approvals" },
  { label: "Knowledge", icon: Database, path: "/knowledge" },
  { label: "Audit Logs", icon: ListChecks, path: "/audit-logs" },
  { label: "Settings", icon: Gear, path: "/settings/models" },
] as const;

interface SidebarProps {
  currentPath: string;
  onNavigate: (path: string) => void;
}

export function Sidebar({ currentPath, onNavigate }: SidebarProps) {
  return (
    <aside className="dashboard-sidebar flex flex-col border-r border-zinc-800 bg-zinc-950">
      {/* Brand */}
      <div className="flex h-14 items-center gap-2.5 border-b border-zinc-800 px-5">
        <Stack size={22} weight="bold" className="text-teal-400" />
        <span className="text-sm font-semibold tracking-tight text-zinc-100">
          HumanGate AI
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = currentPath.startsWith(item.path);
            return (
              <li key={item.path}>
                <button
                  onClick={() => onNavigate(item.path)}
                  className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-zinc-800 text-zinc-100"
                      : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
                  }`}
                >
                  <item.icon size={18} weight={isActive ? "fill" : "regular"} />
                  {item.label}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="border-t border-zinc-800 px-5 py-3">
        <p className="text-xs text-zinc-600">v0.1.0</p>
      </div>
    </aside>
  );
}
