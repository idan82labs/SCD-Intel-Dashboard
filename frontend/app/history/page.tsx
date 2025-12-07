"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { listResearch } from "@/lib/api-client";
import { ArrowLeft, Search, Microscope, Clock, CheckCircle2 } from "lucide-react";
import Link from "next/link";

interface ResearchSummary {
  id: string;
  query: string;
  status: string;
  created_at: string;
  has_report: boolean;
}

export default function HistoryPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<ResearchSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await listResearch();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error("Failed to load sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredSessions = sessions.filter((session) =>
    session.query.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const statusConfig: Record<string, { label: string; variant: "default" | "secondary" | "outline" }> = {
    complete: { label: "Complete", variant: "default" },
    executing: { label: "In Progress", variant: "secondary" },
    error: { label: "Error", variant: "outline" },
    clarifying: { label: "Draft", variant: "secondary" },
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div className="flex items-center gap-2">
              <Microscope className="h-5 w-5 text-primary" />
              <span className="font-semibold">Research History</span>
            </div>
          </div>
          <Link href="/">
            <Button>New Research</Button>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        {/* Search */}
        <div className="max-w-md mb-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search research..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Sessions List */}
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-1/4" />
                </CardHeader>
              </Card>
            ))}
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="text-center py-12">
            <Microscope className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">No research found</h2>
            <p className="text-muted-foreground mb-4">
              {searchQuery
                ? "Try a different search term"
                : "Start your first research to see it here"}
            </p>
            <Link href="/">
              <Button>Start Research</Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredSessions.map((session) => {
              const status = statusConfig[session.status] || statusConfig.clarifying;
              const date = new Date(session.created_at);

              return (
                <Card
                  key={session.id}
                  className="cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => router.push(`/research/${session.id}`)}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <CardTitle className="text-lg">{session.query}</CardTitle>
                        <CardDescription className="flex items-center gap-4">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {date.toLocaleDateString()} {date.toLocaleTimeString()}
                          </span>
                          {session.has_report && (
                            <span className="flex items-center gap-1 text-green-600">
                              <CheckCircle2 className="h-3 w-3" />
                              Report available
                            </span>
                          )}
                        </CardDescription>
                      </div>
                      <Badge variant={status.variant}>{status.label}</Badge>
                    </div>
                  </CardHeader>
                </Card>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
