"use client";

export default function TypingIndicator() {
  return (
    <div
      className="flex items-start gap-3 px-4 py-2 animate-message-in animate-typing-pulse"
      role="status"
      aria-label="Assistant is typing"
    >
      <div className="w-8 h-8 rounded-full bg-meridian-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
        M
      </div>
      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1.5 items-center">
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
          <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}
