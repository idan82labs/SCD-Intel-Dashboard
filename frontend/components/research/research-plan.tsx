"use client";

import { ResearchPlan, ResearchPhase } from "@/types/research";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Building2,
  FileText,
  Newspaper,
  Clock,
  CheckCircle2,
} from "lucide-react";

interface ResearchPlanViewProps {
  plan: ResearchPlan;
  compact?: boolean;
}

const phaseIcons: Record<string, React.ElementType> = {
  market: Search,
  competitive: Building2,
  technology: FileText,
  news: Newspaper,
  default: Search,
};

function getPhaseIcon(phaseName: string) {
  const name = phaseName.toLowerCase();
  if (name.includes("market")) return Search;
  if (name.includes("compet")) return Building2;
  if (name.includes("tech") || name.includes("patent")) return FileText;
  if (name.includes("news")) return Newspaper;
  return Search;
}

export function ResearchPlanView({ plan, compact = false }: ResearchPlanViewProps) {
  if (compact) {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{plan.title}</h3>
          <Badge variant="secondary">
            <Clock className="h-3 w-3 mr-1" />
            ~{plan.estimated_time_minutes} min
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">{plan.objective}</p>
        <div className="space-y-2">
          {plan.phases.map((phase, index) => (
            <PhaseCompact key={index} phase={phase} index={index} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{plan.title}</CardTitle>
          <Badge variant="secondary">
            <Clock className="h-3 w-3 mr-1" />
            ~{plan.estimated_time_minutes} min
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">{plan.objective}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {plan.phases.map((phase, index) => (
          <PhaseCard key={index} phase={phase} index={index} />
        ))}

        {plan.deliverables.length > 0 && (
          <div className="pt-4 border-t">
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              Deliverables
            </h4>
            <ul className="grid grid-cols-2 gap-2">
              {plan.deliverables.map((item, index) => (
                <li
                  key={index}
                  className="text-sm text-muted-foreground flex items-center gap-2"
                >
                  <span className="w-1.5 h-1.5 bg-primary rounded-full" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PhaseCard({ phase, index }: { phase: ResearchPhase; index: number }) {
  const Icon = getPhaseIcon(phase.name);

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
          <Icon className="h-4 w-4 text-primary" />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">
              Phase {index + 1}: {phase.name}
            </h4>
            <span className="text-xs text-muted-foreground">
              ~{phase.estimated_time_minutes} min
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {phase.description}
          </p>
          <ul className="mt-2 space-y-1">
            {phase.tasks.map((task, taskIndex) => (
              <li
                key={taskIndex}
                className="text-sm flex items-center gap-2"
              >
                <span className="w-1 h-1 bg-muted-foreground rounded-full" />
                <span className="text-muted-foreground">{task.description}</span>
                <Badge variant="outline" className="text-xs ml-auto">
                  {task.source}
                </Badge>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function PhaseCompact({ phase, index }: { phase: ResearchPhase; index: number }) {
  const Icon = getPhaseIcon(phase.name);

  return (
    <div className="flex items-center gap-3 p-2 rounded-lg bg-muted/50">
      <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
        <Icon className="h-3 w-3 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <span className="text-sm font-medium">Phase {index + 1}: {phase.name}</span>
        <span className="text-xs text-muted-foreground ml-2">
          ({phase.tasks.length} tasks)
        </span>
      </div>
      <span className="text-xs text-muted-foreground">
        ~{phase.estimated_time_minutes}m
      </span>
    </div>
  );
}
