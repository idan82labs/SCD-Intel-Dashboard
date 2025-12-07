"use client";

import { Message } from "@/types/research";
import { cn } from "@/lib/utils";
import { User, Bot } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
  showAvatar?: boolean;
}

export function MessageBubble({ message, showAvatar = true }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")}
    >
      {/* Avatar */}
      {!isUser && showAvatar && (
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
          <Bot className="h-4 w-4 text-primary" />
        </div>
      )}
      {!isUser && !showAvatar && <div className="w-8" />}

      {/* Message Content */}
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-2",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted"
        )}
      >
        <div className="prose prose-sm max-w-none dark:prose-invert">
          {formatContent(message.content)}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && showAvatar && (
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
          <User className="h-4 w-4 text-primary-foreground" />
        </div>
      )}
      {isUser && !showAvatar && <div className="w-8" />}
    </div>
  );
}

function formatContent(content: string) {
  // Simple markdown-like formatting
  const parts = content.split(/(\*\*.*?\*\*|\n)/g);

  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part === "\n") {
      return <br key={i} />;
    }
    return part;
  });
}
