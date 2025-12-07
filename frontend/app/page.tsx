"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Microscope, Building2, FileText, Package, ArrowRight } from "lucide-react";

const quickStarts = [
  {
    label: "Market Analysis",
    icon: Search,
    query: "Analyze the market for",
  },
  {
    label: "Competitor Intel",
    icon: Building2,
    query: "Who are the key competitors in",
  },
  {
    label: "Patent Landscape",
    icon: FileText,
    query: "What patents exist for",
  },
  {
    label: "Supply Chain Map",
    icon: Package,
    query: "Map the supply chain for",
  },
];

const recentResearch = [
  {
    id: "1",
    title: "EV Battery Supply Chain",
    date: "2 days ago",
    status: "complete",
  },
  {
    id: "2",
    title: "AI Chip Competition",
    date: "1 week ago",
    status: "complete",
  },
  {
    id: "3",
    title: "Biotech M&A Landscape",
    date: "2 weeks ago",
    status: "complete",
  },
];

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    try {
      const response = await fetch("/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/research/${data.id}`);
      }
    } catch (error) {
      console.error("Failed to create research:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickStart = (prefix: string) => {
    setQuery(prefix + " ");
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Microscope className="h-6 w-6 text-primary" />
            <span className="font-semibold text-lg">CI Research</span>
          </div>
          <nav className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => router.push("/history")}>
              History
            </Button>
            <Button variant="ghost">Settings</Button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-12">
        <div className="max-w-3xl mx-auto">
          {/* Hero */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-6">
              <Microscope className="h-8 w-8 text-primary" />
            </div>
            <h1 className="text-4xl font-bold mb-4">Research Agent</h1>
            <p className="text-xl text-muted-foreground">
              What would you like to investigate?
            </p>
          </div>

          {/* Search Form */}
          <form onSubmit={handleSubmit} className="mb-8">
            <div className="flex gap-2">
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Competitive landscape for thermal imaging sensors in commercial drones"
                className="flex-1 h-12 text-lg"
                disabled={isLoading}
              />
              <Button type="submit" size="lg" disabled={isLoading || !query.trim()}>
                {isLoading ? (
                  "Starting..."
                ) : (
                  <>
                    Research
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </form>

          {/* Quick Starts */}
          <div className="mb-12">
            <p className="text-sm text-muted-foreground mb-3">Quick starts:</p>
            <div className="flex flex-wrap gap-2">
              {quickStarts.map((item) => (
                <Button
                  key={item.label}
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickStart(item.query)}
                >
                  <item.icon className="h-4 w-4 mr-2" />
                  {item.label}
                </Button>
              ))}
            </div>
          </div>

          {/* Recent Research */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Recent Research</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {recentResearch.map((item) => (
                <Card
                  key={item.id}
                  className="cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => router.push(`/research/${item.id}`)}
                >
                  <CardHeader className="p-4">
                    <CardTitle className="text-base">{item.title}</CardTitle>
                    <CardDescription className="flex items-center justify-between">
                      <span>{item.date}</span>
                      <Badge variant="secondary" className="text-xs">
                        {item.status}
                      </Badge>
                    </CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t py-6">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          CI Research Platform - Powered by Claude
        </div>
      </footer>
    </div>
  );
}
