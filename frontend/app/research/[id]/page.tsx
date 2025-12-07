"use client";

import { useParams } from "next/navigation";
import { useResearch } from "@/lib/hooks/use-research";
import { ChatInterface } from "@/components/chat/chat-interface";
import { ResearchPlanView } from "@/components/research/research-plan";
import { ExecutionView } from "@/components/research/execution-view";
import { ReportViewer } from "@/components/report/report-viewer";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowLeft, Microscope } from "lucide-react";
import Link from "next/link";

export default function ResearchPage() {
  const params = useParams();
  const sessionId = params.id as string;

  const {
    session,
    messages,
    plan,
    report,
    status,
    isLoading,
    error,
    executionProgress,
    sendMessage,
    startExecution,
  } = useResearch(sessionId);

  // Loading state
  if (!session) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header status="loading" />
        <div className="flex-1 flex items-center justify-center">
          <div className="space-y-4 w-full max-w-2xl p-8">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header status="error" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center p-8">
            <h2 className="text-2xl font-bold text-destructive mb-4">Error</h2>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Link href="/">
              <Button>Return Home</Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Render based on status
  return (
    <div className="min-h-screen flex flex-col">
      <Header status={status} query={session.query} />

      <main className="flex-1 flex overflow-hidden">
        {/* Chat/Clarification Phase */}
        {(status === "clarifying" || status === "planning") && (
          <ChatInterface
            messages={messages}
            isLoading={isLoading}
            onSendMessage={sendMessage}
            plan={plan}
            status={status}
            onStartExecution={startExecution}
          />
        )}

        {/* Plan Ready - Waiting for confirmation */}
        {status === "ready" && plan && (
          <div className="flex-1 flex flex-col">
            <div className="flex-1 overflow-auto p-6">
              <div className="max-w-3xl mx-auto">
                <ResearchPlanView plan={plan} />
                <div className="flex gap-4 mt-6 justify-center">
                  <Button variant="outline" size="lg">
                    Modify Plan
                  </Button>
                  <Button size="lg" onClick={startExecution} disabled={isLoading}>
                    {isLoading ? "Starting..." : "Start Research"}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Execution Phase */}
        {(status === "executing" || status === "synthesizing") && plan && (
          <ExecutionView
            plan={plan}
            progress={executionProgress}
            status={status}
          />
        )}

        {/* Report View */}
        {status === "complete" && report && (
          <ReportViewer report={report} sessionId={sessionId} />
        )}
      </main>
    </div>
  );
}

function Header({
  status,
  query,
}: {
  status: string;
  query?: string;
}) {
  const statusLabels: Record<string, { label: string; variant: "default" | "secondary" | "outline" }> = {
    loading: { label: "Loading...", variant: "secondary" },
    created: { label: "Starting", variant: "secondary" },
    clarifying: { label: "Gathering Context", variant: "secondary" },
    planning: { label: "Creating Plan", variant: "secondary" },
    ready: { label: "Plan Ready", variant: "default" },
    executing: { label: "Researching", variant: "default" },
    synthesizing: { label: "Generating Report", variant: "default" },
    complete: { label: "Complete", variant: "outline" },
    error: { label: "Error", variant: "outline" },
  };

  const statusInfo = statusLabels[status] || statusLabels.loading;

  return (
    <header className="border-b bg-background">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex items-center gap-2">
            <Microscope className="h-5 w-5 text-primary" />
            <span className="font-medium truncate max-w-md">
              {query || "New Research"}
            </span>
          </div>
        </div>
        <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
      </div>
    </header>
  );
}
