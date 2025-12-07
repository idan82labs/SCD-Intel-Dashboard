"use client";

import { ResearchPlan, ResearchStatus } from "@/types/research";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  CheckCircle2,
  Circle,
  Loader2,
  Database,
  FileText,
  Sparkles,
} from "lucide-react";

interface ExecutionProgress {
  totalPhases: number;
  currentPhase: number;
  currentPhaseName: string;
  completedTasks: string[];
  totalResults: number;
}

interface ExecutionViewProps {
  plan: ResearchPlan;
  progress: ExecutionProgress;
  status: ResearchStatus;
}

export function ExecutionView({ plan, progress, status }: ExecutionViewProps) {
  const totalTasks = plan.phases.reduce((sum, p) => sum + p.tasks.length, 0);
  const completedTasks = progress.completedTasks.length;
  const progressPercent = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  return (
    <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
      {/* Left Panel - Progress */}
      <div className="lg:w-1/2 border-r flex flex-col">
        <div className="p-6 border-b">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Research Progress</h2>
            <Badge variant={status === "synthesizing" ? "default" : "secondary"}>
              {status === "executing" ? "Collecting Data" : "Generating Report"}
            </Badge>
          </div>
          <Progress value={progressPercent} className="h-2" />
          <div className="flex justify-between mt-2 text-sm text-muted-foreground">
            <span>{Math.round(progressPercent)}% Complete</span>
            <span>
              {completedTasks}/{totalTasks} tasks
            </span>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {plan.phases.map((phase, phaseIndex) => {
              const isActive = phaseIndex === progress.currentPhase;
              const isComplete = phaseIndex < progress.currentPhase;

              return (
                <Card key={phaseIndex} className={isActive ? "border-primary" : ""}>
                  <CardHeader className="py-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      {isComplete ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : isActive ? (
                        <Loader2 className="h-4 w-4 text-primary animate-spin" />
                      ) : (
                        <Circle className="h-4 w-4 text-muted-foreground" />
                      )}
                      Phase {phaseIndex + 1}: {phase.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="py-2">
                    <ul className="space-y-1">
                      {phase.tasks.map((task, taskIndex) => {
                        const taskComplete = progress.completedTasks.includes(
                          task.description
                        );

                        return (
                          <li
                            key={taskIndex}
                            className="flex items-center gap-2 text-sm"
                          >
                            {taskComplete ? (
                              <CheckCircle2 className="h-3 w-3 text-green-500" />
                            ) : isActive ? (
                              <Loader2 className="h-3 w-3 text-muted-foreground animate-spin" />
                            ) : (
                              <Circle className="h-3 w-3 text-muted-foreground" />
                            )}
                            <span
                              className={
                                taskComplete ? "text-muted-foreground" : ""
                              }
                            >
                              {task.description}
                            </span>
                          </li>
                        );
                      })}
                    </ul>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </ScrollArea>
      </div>

      {/* Right Panel - Live Data Preview */}
      <div className="lg:w-1/2 flex flex-col">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold">Live Data Preview</h2>
        </div>

        <div className="flex-1 p-6 flex flex-col items-center justify-center">
          {status === "executing" ? (
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <Database className="h-8 w-8 text-primary animate-pulse" />
              </div>
              <h3 className="font-semibold mb-2">Collecting Data</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Searching across multiple sources...
              </p>
              <div className="flex items-center justify-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span>{progress.totalResults} results</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <Sparkles className="h-8 w-8 text-primary animate-pulse" />
              </div>
              <h3 className="font-semibold mb-2">Synthesizing Report</h3>
              <p className="text-sm text-muted-foreground">
                Analyzing {progress.totalResults} data points...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
