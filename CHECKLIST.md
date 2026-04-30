# Meridian Chatbot — Demo Checklist

## Pre-Demo Setup (Do These the Night Before)

- [ ] `.env` file exists at project root with a valid `ANTHROPIC_API_KEY`
- [ ] Backend starts without errors: `cd api && uvicorn main:app --port 8000`
- [ ] `GET http://localhost:8000/health` returns `{"status":"ok","mcp_connected":true,"tools_loaded":8}`
- [ ] Frontend starts: `npm run dev` at project root
- [ ] `http://localhost:3000` loads the chat UI with the welcome screen
- [ ] Send one test message ("What monitors do you have?") and get a response with tool calls
- [ ] Run the smoke test: `cd api && python scripts/smoke_test.py --url http://localhost:8000`
- [ ] Check Anthropic API credit balance — Haiku 4.5 costs ~$0.001/turn but budget matters
- [ ] Close all unrelated browser tabs (screen share clutter)
- [ ] Silence notifications on your machine

## Demo Day (5 Minutes Before)

- [ ] Restart the backend fresh: `cd api && uvicorn main:app --port 8000`
- [ ] Restart the frontend: `npm run dev`
- [ ] Open `http://localhost:3000` in a clean browser window (or incognito for a fresh session)
- [ ] Verify the welcome screen appears with the 4 suggestion chips
- [ ] Have `docs/demo-scenarios.md` open in a side tab for reference
- [ ] Have the terminal visible but minimized — you'll need it if something goes wrong

## Recommended Demo Flow

1. **Product browsing** (2 min) — Type "What monitors do you have in stock?"
2. **Edge cases** (1 min) — Type "Can you book me a flight?" then "Look up FAKE-9999"
3. **Authentication** (2 min) — Type "Check my order status" (shows auth gate)
4. **Multi-tool** (1 min) — "Compare the 27-inch Monitor Model A and the 32-inch Monitor Model A"
5. **Order placement** (3 min) — Walk through buying a laser printer

See `docs/demo-scenarios.md` for exact messages and expected responses.

## If Something Goes Wrong

### "The bot isn't responding"
**Say:** "The LLM is processing — it sometimes takes a few seconds when multiple tools are involved."
**Do:** Wait 15 seconds. If still nothing, check the terminal for errors. The most likely cause is an Anthropic API key issue.

### "Got a connection error in the chat"
**Say:** "Let me restart the backend — this happens occasionally with long-running connections."
**Do:** Ctrl+C the backend, restart it, refresh the browser. Takes 10 seconds.

### "The MCP server is down" (`mcp_connected: false` in /health)
**Say:** "The external product database is temporarily unreachable — this is why we built graceful degradation into the system."
**Do:** The bot will still respond, just without tool results. Show this as a feature: "Notice it doesn't crash, it tells the user what happened."

### "The bot gave a wrong or weird answer"
**Say:** "LLMs can occasionally misinterpret requests. In production, we'd add guardrails and output validation. Let me try rephrasing."
**Do:** Rephrase and continue. Don't dwell on it.

### "The API key is expired or rate limited"
**Say:** "We're hitting the API rate limit from testing — in production we'd have a dedicated quota."
**Do:** Wait 30 seconds and retry. If the key is actually expired, there's no recovery during the demo — switch to describing the architecture using the code and screenshots.

### General Recovery Strategy
If anything catastrophic happens, pivot to the architecture. Open the code and walk through:
1. `mcp_client.py` — "Here's how we connect to the MCP server and discover tools"
2. `llm_service.py` — "Here's the agentic loop — Claude decides which tools to call"
3. `chat_handler.py` — "Here's session management with the sliding window"
4. Show the tool call pills in the UI — "Even in a failure case, you can see the system is transparent about what it's doing"
