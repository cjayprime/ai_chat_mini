import { ChatMessage, ChatRequest, SSEEvent, ToolCallRecord } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export interface StreamCallbacks {
  onDelta: (text: string) => void;
  onToolStart: (toolName: string) => void;
  onToolResult: (toolName: string, durationMs: number) => void;
  onDone: (toolCalls: ToolCallRecord[]) => void;
  onError: (error: string) => void;
}

export async function sendMessageStream(
  sessionId: string,
  message: string,
  history: ChatMessage[],
  callbacks: StreamCallbacks,
): Promise<void> {
  const body: ChatRequest = {
    session_id: sessionId,
    message,
    history: history.map((m) => ({
      role: m.role,
      content: m.content,
      timestamp: m.timestamp,
    })),
  };

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    callbacks.onError(
      "Unable to reach the server. Please check that the backend is running.",
    );
    return;
  }

  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    callbacks.onError(`Server error (${res.status}): ${detail}`);
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    callbacks.onError("Streaming not supported by browser.");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const jsonStr = line.slice(6).trim();
      if (!jsonStr) continue;

      try {
        const event: SSEEvent = JSON.parse(jsonStr);

        switch (event.type) {
          case "delta":
            callbacks.onDelta(event.content || "");
            break;
          case "tool_start":
            callbacks.onToolStart(event.tool_name || "unknown");
            break;
          case "tool_result":
            callbacks.onToolResult(
              event.tool_name || "unknown",
              event.duration_ms || 0,
            );
            break;
          case "done":
            callbacks.onDone(event.tool_calls || []);
            break;
          case "error":
            callbacks.onError(event.content || "Unknown error");
            break;
        }
      } catch {
        // skip malformed JSON lines
      }
    }
  }
}

export function getSessionId(): string {
  if (typeof window === "undefined") return crypto.randomUUID();

  const key = "meridian_session_id";
  let id = sessionStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem(key, id);
  }
  return id;
}
