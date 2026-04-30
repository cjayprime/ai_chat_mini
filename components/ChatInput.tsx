"use client";

import { useRef, useState, useEffect, KeyboardEvent } from "react";

const MAX_CHARS = 500;

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [charCount, setCharCount] = useState(0);

  useEffect(() => {
    if (!disabled) {
      textareaRef.current?.focus();
    }
  }, [disabled]);

  function handleSubmit() {
    const value = textareaRef.current?.value.trim();
    if (!value || disabled || value.length > MAX_CHARS) return;
    onSend(value);
    if (textareaRef.current) {
      textareaRef.current.value = "";
      textareaRef.current.style.height = "auto";
      setCharCount(0);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleInput() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
    setCharCount(el.value.length);
  }

  const overLimit = charCount > MAX_CHARS;

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3 shrink-0">
      <div className="max-w-3xl mx-auto flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            rows={1}
            placeholder="Type your message..."
            disabled={disabled}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            maxLength={MAX_CHARS + 50}
            aria-label="Message input"
            aria-describedby="char-counter input-hint"
            className={`w-full resize-none rounded-xl border bg-gray-50 px-4 py-2.5 pr-16 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed ${
              overLimit
                ? "border-red-400 focus:ring-red-400"
                : "border-gray-300 focus:ring-meridian-600"
            }`}
          />
          <span
            id="char-counter"
            className={`absolute right-3 bottom-2.5 text-[10px] select-none ${
              overLimit ? "text-red-500 font-medium" : "text-gray-400"
            }`}
          >
            {charCount}/{MAX_CHARS}
          </span>
        </div>
        <button
          onClick={handleSubmit}
          disabled={disabled || overLimit}
          aria-label="Send message"
          className="h-10 w-10 rounded-xl bg-meridian-600 text-white flex items-center justify-center hover:bg-meridian-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"
            />
          </svg>
        </button>
      </div>
      <p id="input-hint" className="text-[10px] text-gray-400 text-center mt-1.5">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}
