"use client";

import { Bot } from "lucide-react";

export function TypingIndicator() {
  return (
    <div className="flex gap-3 justify-start">
      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
        <Bot className="h-4 w-4 text-primary" />
      </div>
      <div className="bg-muted rounded-lg px-4 py-3 flex items-center gap-1">
        <span className="w-2 h-2 bg-muted-foreground/50 rounded-full typing-dot" />
        <span className="w-2 h-2 bg-muted-foreground/50 rounded-full typing-dot" />
        <span className="w-2 h-2 bg-muted-foreground/50 rounded-full typing-dot" />
      </div>
    </div>
  );
}
