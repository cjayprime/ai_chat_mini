export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  toolCalls?: ToolCallRecord[];
}

export interface ToolCallRecord {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: string;
  duration_ms: number;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  history: { role: string; content: string; timestamp: string }[];
}

export interface ChatResponse {
  session_id: string;
  message: string;
  tool_calls_made: ToolCallRecord[];
  timestamp: string;
}

export interface SSEEvent {
  type: "delta" | "tool_start" | "tool_result" | "done" | "error";
  content?: string;
  tool_name?: string;
  arguments?: Record<string, unknown>;
  duration_ms?: number;
  tool_calls?: ToolCallRecord[];
}
