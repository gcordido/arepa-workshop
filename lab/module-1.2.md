## Module 1.2: Live tools and a store persona (12 minutes)

An agent that only chats cannot register a customer or place an order.
The Arepa Lab **MCP server** provides those tools and the store's persona.

> Model Context Protocol (MCP) connects clients to servers exposing tools,
> prompts, and resources. A server does not have to publish all three.
> Our store publishes tools and prompts over Streamable HTTP.

### Step A: connect the tools

Check that the root `.env` includes:

```dotenv
AREPA_MCP_URL="https://ca-arepa-mcp.yellowbeach-684b8340.eastus.azurecontainerapps.io/mcp/"
```

In `agent.py`, find the MCP connection and the agent's tool list:

```python
store = MCPStreamableHTTPTool(
    name="arepa-store",
    url=setting("AREPA_MCP_URL"),
    parse_tool_results=orders.parse_result,
)
await store.connect()
tools.append(store)
```

The parser preserves a confirmed order's public summary fields for Module
1.4. The server still owns validation and ordering. The async cleanup closes
connections when the program exits or raises an error.

Run the tools-only checkpoint from `arepa-agent/`:

```powershell
python agent.py --module 1.2 --tools-only --trace
```

Ask `Show today's menu only; do not register me or place an order.`
Watch for a `[tool]` line naming `list_arepas`. Check that the response uses
the returned names and stock labels, not invented products or raw counts.

Do not order in this step. Type `exit`.

### Step B: load the store's persona

The server publishes two prompts:

- `agent_instructions`: the ordering flow, voice, privacy, and safety rules.
- `welcome_banner`: the greeting printed by the client at startup.

Find these lines in `agent.py`:

```python
instructions = await store.get_prompt("agent_instructions")
banner = await store.get_prompt("welcome_banner")
```

The instructions go into `Agent(...)`; the banner is printed once. Tools
make actions possible. Instructions tell the agent how to use them.
The tools-only comparison omits these explicit prompt calls; the server may
also supply guidance during connection, so do not expect a particular voice.

Run:

```powershell
python agent.py --module 1.2 --trace
```

### Register once, or return with your ID

Answer the agent's first question:

1. **New customer:** provide your first name, last name, and city. The agent
   calls `register_customer` and shows your permanent eight-character ID.
2. **Returning customer:** provide your existing ID. The agent calls
   `get_customer` before continuing.

> **Copy your customer ID now.** Reuse it for the rest of the lab.
>
> @lab.TextBox(customerID)

Do not create a second identity to get another real order.

### Make one explicit order

Choose an item from the current menu by name or number. The agent should
show display names and qualitative stock, while keeping machine IDs internal.

Choose the order kind:

- **Test:** practice only; no stock is consumed and there is no pickup.
- **Real:** an actual arepa for pickup. Each customer can receive one real
  arepa. If you have already used yours, choose test.

Open the dashboard:
`https://ca-arepa-mcp.yellowbeach-684b8340.eastus.azurecontainerapps.io/dashboard`

Read the current six-character voucher **last**, after the item and kind
are chosen. Both kinds require it. Let the agent place the order immediately.
If the code is rejected, reread the screen; do not keep guessing.

Watch the `order_arepa` call and its response:

- A real order is collected only when the dashboard says **Ready for pickup**.
  Look for your displayed board name and follow staff directions.
- A test order completes automatically in the test feed. It is not tracked
  as an active real order by `check_order_status`.
- A failed tool call is not a successful order. Follow the agent's correction
  prompt. If stock changed, choose again from a refreshed menu.

**Keep this process open for Module 1.4 if convenient.** The client captures
the confirmed order result only in memory. If you need to stop, Module 1.4
also has a simulated example; no second real order is needed.

**Checkpoint 3.** Your agent used the live tools and server persona to
complete an explicit test or real order, and you saved your customer ID.

<!-- Replace the Sparkles dashboard screenshot with an Arepa Lab capture.
Do not publish the old image or a voucher that appears reusable. -->
