# Meridian Chatbot — Demo Scenarios

Five scripted flows for the live presentation. Each scenario lists the exact messages to send, the MCP tools the bot should invoke, and what to look for in the response.

---

## Scenario A: New Customer Browsing

**Goal:** Show product discovery works without authentication.

| Step | You type | Expected tool calls | What to look for in the response |
|------|----------|---------------------|----------------------------------|
| 1 | `What monitors do you have in stock?` | `list_products(category="Monitors")` | Lists monitors with SKU, price, stock. Should show MON-0053, MON-0056, MON-0061, etc. |
| 2 | `Tell me more about the 24-inch Model D` | `get_product(sku="MON-0054")` | Shows full details: $166.85, 7 units in stock, Active status. |
| 3 | `Do you have any wireless routers?` | `list_products(category="Networking")` or `search_products(query="wireless router")` | Lists NET-0181 through NET-0184+ with prices ranging $141–$264. |

**Key point to highlight:** No authentication was needed — product browsing is open to everyone.

---

## Scenario B: Returning Customer Order Lookup

**Goal:** Show the authentication gate and order tracking.

| Step | You type | Expected tool calls | What to look for in the response |
|------|----------|---------------------|----------------------------------|
| 1 | `I want to check my order status` | (none) | Bot asks for email and 4-digit PIN. Does NOT call any tool yet. |
| 2 | `My email is jane@example.com and PIN is 1234` | `verify_customer_pin(email="jane@example.com", pin="1234")` | Either succeeds (shows customer name, then asks which order) or fails gracefully ("I couldn't verify that — please double-check your email and PIN"). |
| 3 | *(If auth succeeded)* `Show me my recent orders` | `list_orders(customer_id="<uuid>")` | Lists orders with status (fulfilled/submitted/draft), totals, dates. |
| 4 | *(Pick an order ID from the list)* `What's in order <order-id>?` | `get_order(order_id="<order-id>")` | Shows line items with SKUs, quantities, unit prices. |

**Key point to highlight:** The bot refused to look up orders until the customer was verified — that's the system prompt auth gate working.

**If auth fails:** That's actually a good demo moment. Say: "Notice it handled the failure gracefully and told us what to do next."

---

## Scenario C: Product Comparison

**Goal:** Show multiple sequential tool calls in a single turn.

| Step | You type | Expected tool calls | What to look for in the response |
|------|----------|---------------------|----------------------------------|
| 1 | `Compare the 27-inch Monitor Model A and the 32-inch Monitor Model A` | `get_product(sku="MON-0056")` then `get_product(sku="MON-0061")` | Two tool call pills appear. Bot presents a comparison: MON-0056 at $484.14 (32 units) vs MON-0061 at $831.92 (11 units). |
| 2 | `Which one is better value for the price?` | (none — LLM reasoning) | Bot gives an opinion based on the data it already retrieved, no new tool calls. |

**Key point to highlight:** The bot made two tool calls in one turn and synthesized the results. The tool call pills in the UI show exactly what happened.

---

## Scenario D: Full Order Placement

**Goal:** Walk through the complete purchase journey end to end.

| Step | You type | Expected tool calls | What to look for in the response |
|------|----------|---------------------|----------------------------------|
| 1 | `I'd like to buy a laser printer` | `list_products(category="Printers")` or `search_products(query="laser printer")` | Shows printers: PRI-0091 ($366.23), PRI-0092 ($739.64), PRI-0093 ($378.87), etc. |
| 2 | `I'll take the PRI-0091, one unit` | (none) | Bot asks for authentication before placing the order. |
| 3 | `My email is <email> and PIN is <pin>` | `verify_customer_pin(email=..., pin=...)` | Authenticates, then confirms: "You'd like to order 1x PRI-0091 Laser Printer Model A at $366.23. Shall I place this order?" |
| 4 | `Yes, go ahead` | `create_order(customer_id="<uuid>", items=[{sku: "PRI-0091", quantity: 1, unit_price: "366.23", currency: "USD"}])` | Order confirmation with order ID, total, "submitted" status. |
| 5 | `Show me that order` | `get_order(order_id="<new-order-id>")` | Full order details confirming the line item. |

**Key point to highlight:** Five turns, four tool calls, three different tools — but the user experience feels like a natural conversation.

**If create_order fails (InsufficientInventoryError):** Say: "The MCP server validates inventory atomically — it won't let us oversell."

---

## Scenario E: Edge Cases and Graceful Failures

**Goal:** Show the bot handles out-of-scope requests and tool errors without breaking.

| Step | You type | Expected tool calls | What to look for in the response |
|------|----------|---------------------|----------------------------------|
| 1 | `Can you book me a flight to Tokyo?` | (none) | Politely declines — "I'm the Meridian Electronics support assistant. I can help with products, orders, and account questions, but I can't book flights." |
| 2 | `What's the weather like today?` | (none) | Same — stays in scope without calling any tool. |
| 3 | `Look up product SKU FAKE-9999` | `get_product(sku="FAKE-9999")` | Tool returns an error. Bot says something like: "I couldn't find a product with SKU FAKE-9999. Would you like me to search for something specific?" |
| 4 | `Search for quantum computers` | `search_products(query="quantum computers")` | Returns empty results. Bot says: "No products matched that search. We carry Computers, Monitors, Printers, Networking gear, and Accessories — want me to browse any of those?" |

**Key point to highlight:** The bot never crashes, never hallucinates products, and always offers a next step.

---

## Presentation Flow (Recommended Order)

1. **Start with Scenario A** (2 min) — shows the core product lookup works
2. **Then Scenario E, Step 1–2** (1 min) — shows it stays in scope
3. **Then Scenario B** (2 min) — shows authentication
4. **Then Scenario C** (1 min) — shows multi-tool calls
5. **End with Scenario D** (3 min) — the grand finale, full order placement

Total: ~9 minutes of live demo.
