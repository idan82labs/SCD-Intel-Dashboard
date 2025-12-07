"use client";

import { useState, useRef, useEffect } from "react";
import { Message, ResearchPlan, ResearchStatus } from "@/types/research";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { MessageBubble } from "./message-bubble";
import { TypingIndicator } from "./typing-indicator";
import { ResearchPlanView } from "@/components/research/research-plan";
import { Send, Paperclip } from "lucide-react";

interface ChatInterfaceProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (message: string) => Promise<void>;
  plan: ResearchPlan | null;
  status: ResearchStatus;
  onStartExecution: () => Promise<void>;
}

export function ChatInterface({
  messages,
  isLoading,
  onSendMessage,
  plan,
  status,
  onStartExecution,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      const scrollElement = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [messages, isLoading]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const message = input;
    setInput("");
    await onSendMessage(message);
  };

  return (
    <div className="flex-1 flex flex-col">
      {/* Messages Area */}
      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        <div className="space-y-4 max-w-3xl mx-auto pb-4">
          {messages.map((message, index) => (
            <MessageBubble
              key={index}
              message={message}
              showAvatar={
                index === 0 || messages[index - 1]?.role !== message.role
              }
            />
          ))}

          {isLoading && <TypingIndicator />}

          {/* Show plan when ready */}
          {plan && status === "ready" && (
            <Card className="p-4 mt-4 border-primary/50">
              <ResearchPlanView plan={plan} compact />
              <div className="flex gap-2 mt-4">
                <Button variant="outline" className="flex-1">
                  Modify Plan
                </Button>
                <Button className="flex-1" onClick={onStartExecution}>
                  Start Research
                </Button>
              </div>
            </Card>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t p-4 bg-background">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className="flex gap-2">
            <Button type="button" variant="ghost" size="icon" disabled>
              <Paperclip className="h-4 w-4" />
            </Button>
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                status === "clarifying"
                  ? "Type your response..."
                  : "Ask a follow-up question..."
              }
              disabled={isLoading || status === "executing"}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
