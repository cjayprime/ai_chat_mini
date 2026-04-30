"use client";

import { useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { ChatMessage } from "@/lib/types";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

const SUGGESTIONS = [
  "Check my order status",
  "What monitors do you have in stock?",
  "I need help with a return",
  "Look up my account",
];

const TOOL_LABELS: Record<string, string> = {
  list_products: "Browsing products",
  get_product: "Looking up product details",
  search_products: "Searching catalog",
  get_customer: "Retrieving customer info",
  verify_customer_pin: "Verifying identity",
  list_orders: "Checking order history",
  get_order: "Loading order details",
  create_order: "Placing order",
};

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  streamingText: string;
  activeTools: string[];
  onSuggestionClick: (text: string) => void;
}

export default function ChatWindow({
  messages,
  isLoading,
  streamingText,
  activeTools,
  onSuggestionClick,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading, streamingText]);

  const showStreaming = isLoading && (streamingText || activeTools.length > 0);
  const showTypingDots =
    isLoading && !streamingText && activeTools.length === 0;

  return (
    <div
      className="flex-1 overflow-y-auto bg-gray-50"
      role="log"
      aria-label="Chat messages"
    >
      <div className="max-w-3xl mx-auto py-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center py-20 px-4 text-center animate-message-in">
            <div className="w-16 h-16 rounded-2xl bg-meridian-600 flex items-center justify-center text-white text-2xl font-bold mb-4">
              Mzz
            </div>
            <h2 className="text-lg font-semibold text-gray-800 mb-2">
              Hi, I&apos;m Meridian Support
            </h2>
            <p className="text-sm text-gray-500 max-w-md">
              How can I help you today? I can browse products, check orders,
              place new orders, and manage your account.
            </p>
            <div className="flex flex-wrap gap-2 mt-6 justify-center">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => onSuggestionClick(suggestion)}
                  className="text-xs border border-meridian-200 text-meridian-700 rounded-full px-3.5 py-1.5 hover:bg-meridian-50 hover:border-meridian-300 transition-colors focus:outline-none focus:ring-2 focus:ring-meridian-600 focus:ring-offset-1"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {showStreaming && (
          <div className="flex items-start gap-3 px-4 py-2 animate-message-in">
            <div className="w-8 h-8 rounded-full bg-meridian-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
              M
            </div>
            <div className="max-w-[75%] flex flex-col gap-1.5 items-start">
              {activeTools.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-0.5">
                  {activeTools.map((tool, i) => (
                    <span
                      key={`${tool}-${i}`}
                      className="inline-flex items-center gap-1.5 text-xs bg-meridian-50 text-meridian-700 border border-meridian-200 rounded-full px-2.5 py-0.5 animate-typing-pulse"
                    >
                      <svg
                        className="w-3 h-3 animate-spin"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={2}
                        stroke="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
                        />
                      </svg>
                      {TOOL_LABELS[tool] || tool}...
                    </span>
                  ))}
                </div>
              )}
              {streamingText && (
                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-2.5 shadow-sm break-words text-gray-800 prose-chat">
                  <ReactMarkdown>{streamingText}</ReactMarkdown>
                  <span className="inline-block w-1.5 h-4 bg-meridian-600 ml-0.5 animate-pulse align-middle" />
                </div>
              )}
            </div>
          </div>
        )}

        {showTypingDots && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
