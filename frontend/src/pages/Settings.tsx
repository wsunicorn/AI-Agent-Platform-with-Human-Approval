/** Settings page: Models, Tools, and Guardrails. */

import { Gear, Robot, Wrench, ShieldCheck } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import {
  fetchModelConfigs,
  fetchTools,
  fetchGuardrailPolicies,
} from "../lib/api";
import { StatusBadge } from "../components/ui/StatusBadge";
import { ErrorState, LoadingState } from "../components/ui/States";
import type { ModelConfig, ToolConfig } from "../types/models";

type SettingsTab = "models" | "tools" | "guardrails";

export function SettingsPage() {
  const [tab, setTab] = useState<SettingsTab>("models");

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-zinc-100">Settings</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Configure models, tools, and guardrail policies
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-1 rounded-lg bg-zinc-900 p-1">
        {[
          { key: "models" as const, label: "Models", icon: Robot },
          { key: "tools" as const, label: "Tools", icon: Wrench },
          { key: "guardrails" as const, label: "Guardrails", icon: ShieldCheck },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? "bg-zinc-700 text-zinc-100"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            <t.icon size={16} />
            {t.label}
          </button>
        ))}
      </div>

      {tab === "models" && <ModelConfigTab />}
      {tab === "tools" && <ToolConfigTab />}
      {tab === "guardrails" && <GuardrailTab />}
    </div>
  );
}

function ModelConfigTab() {
  const { data, isLoading, error } = useQuery<ModelConfig[]>({
    queryKey: ["model-configs"],
    queryFn: fetchModelConfigs,
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message={String(error)} />;

  return (
    <div className="space-y-2">
      {(data ?? []).map((config: ModelConfig) => (
        <div
          key={config.id}
          className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3"
        >
          <div className="flex items-center gap-3">
            <Robot size={18} className="text-zinc-500" />
            <div>
              <p className="text-sm font-medium text-zinc-200">
                {config.model_name}
              </p>
              <p className="mt-0.5 text-xs text-zinc-500">
                {config.provider} · {config.purpose} · {config.mode}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {config.is_default && (
              <span className="rounded-md bg-teal-500/15 px-2 py-0.5 text-xs font-medium text-teal-400 border border-teal-500/30">
                default
              </span>
            )}
            <span
              className={`h-2 w-2 rounded-full ${
                config.is_enabled ? "bg-emerald-400" : "bg-zinc-600"
              }`}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function ToolConfigTab() {
  const { data, isLoading, error } = useQuery<ToolConfig[]>({
    queryKey: ["tools"],
    queryFn: fetchTools,
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message={String(error)} />;

  return (
    <div className="space-y-2">
      {(data ?? []).map((tool: ToolConfig) => (
        <div
          key={tool.name}
          className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3"
        >
          <div className="flex items-center gap-3">
            <Wrench size={18} className="text-zinc-500" />
            <div>
              <p className="text-sm font-medium text-zinc-200">
                {tool.name.replace(/_/g, " ")}
              </p>
              {tool.description && (
                <p className="mt-0.5 text-xs text-zinc-500">
                  {tool.description}
                </p>
              )}
            </div>
          </div>
          <StatusBadge status={tool.sensitivity} />
        </div>
      ))}
    </div>
  );
}

function GuardrailTab() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["guardrail-policies"],
    queryFn: fetchGuardrailPolicies,
  });

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState message={String(error)} />;

  const policies = data as Record<string, unknown> | undefined;

  return (
    <div className="space-y-4">
      {["safe_tools", "approval_required_tools", "blocked_tools"].map(
        (category) => {
          const tools = (policies?.[category] ?? []) as string[];
          const label = category.replace(/_/g, " ");
          return (
            <div key={category}>
              <h3 className="mb-2 text-sm font-semibold text-zinc-300 capitalize">
                {label}
              </h3>
              <div className="flex flex-wrap gap-2">
                {tools.map((tool) => (
                  <span
                    key={tool}
                    className="rounded-md bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-300"
                  >
                    {tool.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>
          );
        }
      )}
    </div>
  );
}
