"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Header from "@/components/Header";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import { sendMessageStream, getSessionId } from "@/lib/api";
import { ChatMessage, ToolCallRecord } from "@/lib/types";

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [streamingText, setStreamingText] = useState<string>("");
  const [activeTools, setActiveTools] = useState<string[]>([]);

  const streamingTextRef = useRef("");
  const toolCallsRef = useRef<ToolCallRecord[]>([]);

  useEffect(() => {
    setSessionId(getSessionId());
  }, []);

  const handleSend = useCallback(
    async (text: string) => {
      if (!sessionId) return;

      setError(null);
      setStreamingText("");
      setActiveTools([]);
      streamingTextRef.current = "";
      toolCallsRef.current = [];

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      await sendMessageStream(sessionId, text, messages, {
        onDelta: (content) => {
          streamingTextRef.current += content;
          setStreamingText(streamingTextRef.current);
        },
        onToolStart: (toolName) => {
          setActiveTools((prev) => [...prev, toolName]);
        },
        onToolResult: (toolName, durationMs) => {
          toolCallsRef.current.push({
            tool_name: toolName,
            arguments: {},
            result: "",
            duration_ms: durationMs,
          });
          setActiveTools((prev) => prev.filter((t) => t !== toolName));
        },
        onDone: (toolCalls) => {
          const finalToolCalls =
            toolCalls.length > 0 ? toolCalls : toolCallsRef.current;

          const assistantMsg: ChatMessage = {
            id: crypto.randomUUID(),
            role: "assistant",
            content: streamingTextRef.current.trim(),
            timestamp: new Date().toISOString(),
            toolCalls:
              finalToolCalls.length > 0 ? finalToolCalls : undefined,
          };

          setMessages((prev) => [...prev, assistantMsg]);
          setStreamingText("");
          streamingTextRef.current = "";
          setActiveTools([]);
          setIsLoading(false);
        },
        onError: (errorMsg) => {
          setError(errorMsg);
          setStreamingText("");
          streamingTextRef.current = "";
          setActiveTools([]);
          setIsLoading(false);
        },
      });
    },
    [sessionId, isLoading, messages],
  );

  return (
    <div className="h-full flex flex-col">
      <Header />

      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        streamingText={streamingText}
        activeTools={activeTools}
        onSuggestionClick={handleSend}
      />

      {error && (
        <div
          className="bg-red-50 border-t border-red-200 px-4 py-2.5 text-sm text-red-700 flex items-center justify-between shrink-0"
          role="alert"
        >
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="text-red-500 hover:text-red-700 text-xs font-medium ml-4"
            aria-label="Dismiss error"
          >
            Dismiss
          </button>
        </div>
      )}

      <ChatInput onSend={handleSend} disabled={!sessionId} />
    </div>
  );
}
