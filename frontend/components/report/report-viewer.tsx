"use client";

import { useState } from "react";
import { Report } from "@/types/research";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChartWrapper } from "@/components/visualizations/chart-wrapper";
import { ExportDialog } from "./export-dialog";
import {
  Download,
  Share2,
  FileText,
  Lightbulb,
  BarChart3,
  ChevronRight,
} from "lucide-react";

interface ReportViewerProps {
  report: Report;
  sessionId: string;
}

export function ReportViewer({ report, sessionId }: ReportViewerProps) {
  const [activeSection, setActiveSection] = useState(0);
  const [showExport, setShowExport] = useState(false);

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Table of Contents Sidebar */}
      <aside className="w-64 border-r bg-muted/30 hidden lg:block">
        <div className="p-4">
          <h3 className="font-semibold mb-4">Contents</h3>
          <nav className="space-y-1">
            <button
              onClick={() => setActiveSection(-1)}
              className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                activeSection === -1
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              }`}
            >
              Executive Summary
            </button>
            <button
              onClick={() => setActiveSection(-2)}
              className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                activeSection === -2
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              }`}
            >
              Key Findings
            </button>
            {report.sections.map((section, index) => (
              <button
                key={index}
                onClick={() => setActiveSection(index)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors flex items-center ${
                  activeSection === index
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-muted"
                }`}
              >
                <ChevronRight className="h-3 w-3 mr-2" />
                {section.title}
              </button>
            ))}
            <button
              onClick={() => setActiveSection(-3)}
              className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${
                activeSection === -3
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-muted"
              }`}
            >
              Recommendations
            </button>
          </nav>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="border-b p-4 flex items-center justify-between bg-background">
          <div>
            <h1 className="text-xl font-bold">{report.title}</h1>
            <p className="text-sm text-muted-foreground">
              Generated {new Date(report.generated_at).toLocaleString()}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowExport(true)}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Button variant="outline" size="sm">
              <Share2 className="h-4 w-4 mr-2" />
              Share
            </Button>
          </div>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1">
          <div className="p-6 max-w-4xl mx-auto space-y-8">
            {/* Executive Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Executive Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  {formatContent(report.executive_summary)}
                </div>
              </CardContent>
            </Card>

            {/* Key Findings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5" />
                  Key Findings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {report.key_findings.map((finding, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <Badge variant="outline" className="mt-0.5 flex-shrink-0">
                        {index + 1}
                      </Badge>
                      <span>{finding}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Detailed Sections */}
            {report.sections.map((section, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle>{section.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Narrative Content */}
                  <div className="prose prose-sm max-w-none">
                    {formatContent(section.content)}
                  </div>

                  {/* Visualizations */}
                  {section.visualizations?.map((viz, vizIndex) => (
                    <div key={vizIndex} className="mt-6">
                      <h4 className="text-sm font-medium mb-2">{viz.title}</h4>
                      {viz.description && (
                        <p className="text-sm text-muted-foreground mb-4">
                          {viz.description}
                        </p>
                      )}
                      <ChartWrapper type={viz.type} data={viz.data} />
                    </div>
                  ))}
                </CardContent>
              </Card>
            ))}

            {/* Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {report.recommendations.map((rec, index) => (
                    <li
                      key={index}
                      className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg"
                    >
                      <div className="h-6 w-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium flex-shrink-0">
                        {index + 1}
                      </div>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        </ScrollArea>
      </main>

      {/* Export Dialog */}
      <ExportDialog
        open={showExport}
        onClose={() => setShowExport(false)}
        sessionId={sessionId}
      />
    </div>
  );
}

function formatContent(text: string) {
  // Split by paragraphs
  const paragraphs = text.split(/\n\n+/);

  return paragraphs.map((para, i) => {
    // Handle bold text
    const formatted = para.split(/(\*\*.*?\*\*)/g).map((part, j) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });

    return <p key={i} className="mb-4 last:mb-0">{formatted}</p>;
  });
}
