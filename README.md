# Meridian Electronics — Customer Support Chatbot

AI-powered support chatbot for Meridian Electronics. Uses Claude (Haiku 4.5) with MCP tool calling to browse products, authenticate customers, place orders, and track shipments.

## Architecture

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   Next.js UI     │ POST  │  FastAPI Backend  │  MCP  │  Order MCP       │
│   (port 3000)    │──────>│  (port 8000)      │──────>│  (Cloud Run)     │
│                  │  /chat│                    │       │                  │
│  - Chat window   │<──────│  - Agentic loop   │       │  - list_products │
│  - Suggestions   │  JSON │  - Session mgmt   │       │  - get_product   │
│  - Tool pills    │       │  - History window  │       │  - search_prods  │
└──────────────────┘       │                    │       │  - get_customer  │
                           │        │           │       │  - verify_pin    │
                           │        ▼           │       │  - list_orders   │
                           │  ┌───────────┐     │       │  - get_order     │
                           │  │ Anthropic │     │       │  - create_order  │
                           │  │ Claude    │     │       └──────────────────┘
                           │  │ Haiku 4.5 │     │
                           │  └───────────┘     │
                           └──────────────────┘
```

## Quick Start

### 1. Clone and configure

```bash
git clone <repo-url> && cd assessment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2a. Run with Docker (recommended)

```bash
docker compose up --build
```

Backend is available at `http://localhost:8000`. Health check: `GET /health`.

### 2b. Run without Docker

**Backend:**

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## API Endpoints

| Method | Path                    | Description                 |
|--------|-------------------------|-----------------------------|
| POST   | `/chat`                 | Send a message, get reply   |
| GET    | `/health`               | Backend + MCP status        |
| GET    | `/sessions/{session_id}`| Session metadata (debug)    |

### POST /chat

```json
{
  "session_id": "uuid-here",
  "message": "What monitors do you have?",
  "history": []
}
```

### Response

```json
{
  "session_id": "uuid-here",
  "message": "We have 40 monitors in stock...",
  "tool_calls_made": [
    {
      "tool_name": "list_products",
      "arguments": {"category": "Monitors"},
      "result": "Found 40 products...",
      "duration_ms": 344.1
    }
  ],
  "timestamp": "2026-04-30T12:00:00Z"
}
```

## Running Tests

```bash
cd api
pip install -r requirements.txt pytest pytest-asyncio httpx
pytest tests/ -v
```

## Project Structure

```
assessment/
├── api/                      # FastAPI backend
│   ├── main.py               # App entry, routes, lifespan
│   ├── config.py             # Environment settings
│   ├── models.py             # Pydantic request/response models
│   ├── mcp_client.py         # MCP server connection + tool calls
│   ├── llm_service.py        # Claude agentic loop
│   ├── chat_handler.py       # Session management + orchestration
│   ├── requirements.txt
│   └── Dockerfile
├── app/                      # Next.js pages
├── components/               # React chat UI components
├── lib/                      # Frontend API client + types
├── docker-compose.yml
├── .env.example
└── package.json
```

## Environment Variables

| Variable               | Required | Default                                              |
|------------------------|----------|------------------------------------------------------|
| `ANTHROPIC_API_KEY`    | Yes      | —                                                    |
| `MCP_SERVER_URL`       | No       | `https://order-mcp-74afyau24q-uc.a.run.app/mcp`     |
| `CORS_ORIGINS`         | No       | `*`                                                  |
| `LOG_LEVEL`            | No       | `INFO`                                               |
| `MAX_TOOL_ITERATIONS`  | No       | `10`                                                 |
| `MAX_HISTORY_MESSAGES` | No       | `20`                                                 |
| `SESSION_TTL_MINUTES`  | No       | `30`                                                 |
