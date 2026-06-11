import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Theme } from "@radix-ui/themes";

import { Sidebar } from "../components/layout/Sidebar";
import { TopBar } from "../components/layout/TopBar";
import { TicketInbox } from "../pages/TicketInbox";
import { TicketDetail } from "../pages/TicketDetail";
import { ApprovalQueue } from "../pages/ApprovalQueue";
import { KnowledgeBase } from "../pages/KnowledgeBase";
import { AuditLogExplorer } from "../pages/AuditLogs";
import { SettingsPage } from "../pages/Settings";
import { AgentRunTimeline } from "../pages/AgentRunTimeline";
import { ApprovalDetail } from "../pages/ApprovalDetail";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export function App() {
  const [currentPath, setCurrentPath] = useState<string>("/tickets");
  const [activeTicketId, setActiveTicketId] = useState<string | null>(null);
  const [activeAgentRunId, setActiveAgentRunId] = useState<string | null>(null);
  const [activeApprovalId, setActiveApprovalId] = useState<string | null>(null);

  const renderContent = () => {
    if (activeApprovalId) {
      return (
        <ApprovalDetail
          approvalId={activeApprovalId}
          onBack={() => setActiveApprovalId(null)}
        />
      );
    }

    if (activeAgentRunId) {
      return (
        <AgentRunTimeline
          runId={activeAgentRunId}
          onBack={() => setActiveAgentRunId(null)}
        />
      );
    }

    if (activeTicketId) {
      return (
        <TicketDetail
          ticketId={activeTicketId}
          onBack={() => setActiveTicketId(null)}
          onViewRun={(runId) => setActiveAgentRunId(runId)}
        />
      );
    }

    switch (currentPath) {
      case "/tickets":
        return <TicketInbox onSelectTicket={(id) => setActiveTicketId(id)} />;
      case "/approvals":
        return <ApprovalQueue onSelectApproval={(id) => setActiveApprovalId(id)} />;
      case "/knowledge":
        return <KnowledgeBase />;
      case "/audit-logs":
        return <AuditLogExplorer />;
      case "/settings/models":
      case "/settings":
        return <SettingsPage />;
      default:
        return <TicketInbox onSelectTicket={(id) => setActiveTicketId(id)} />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <Theme appearance="dark" accentColor="teal" grayColor="slate" radius="medium">
        <div className="dashboard-layout bg-zinc-950 text-zinc-100">
          <Sidebar
            currentPath={currentPath}
            onNavigate={(path) => {
              setCurrentPath(path);
              setActiveTicketId(null);
              setActiveAgentRunId(null);
              setActiveApprovalId(null);
            }}
          />
          <TopBar />
          <main className="dashboard-main">
            <div className="mx-auto max-w-[var(--content-max-width)]">
              {renderContent()}
            </div>
          </main>
        </div>
      </Theme>
    </QueryClientProvider>
  );
}
