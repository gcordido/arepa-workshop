## Module 1.4: A structured order summary (6 minutes)

The back office needs predictable JSON, but predictable JSON is not the same
as a true receipt. This demo does not process payments. We will summarize a
confirmed order result without fabricating a price, pickup time, or identifier.

### Read the schema and source check

Open `arepa-agent/receipt.py`. `RECEIPT_SCHEMA` requires:

- The item name from the successful tool result.
- Quantity `1`, because the counter API accepts one item per order.
- The order kind, `test` or `real`.
- Status `confirmed`.
- `payment_processed: false`.

Internal order IDs and item slugs are not included. Prices and pickup times
are omitted because this result does not establish them.

Find the API's schema configuration:

```python
output_config={"format": {"type": "json_schema", "schema": RECEIPT_SCHEMA}}
```

This is the keyword argument to `messages.create` inside `receipt.py`,
not an additional edit to `agent.py`. Inspect the prepared helper rather
than reimplementing it during the lab.

The helper selects a text block, parses JSON, validates the schema locally,
and compares every field with the expected summary from the source result.
It raises an error if the output disagrees. Schema validity alone would not
catch the wrong item name.

### Add the receipt command

Exit the previous agent. From `arepa-agent/`, the **fast path** is to back
up your current file and copy the completed version:

```powershell
Copy-Item agent.py agent-before-1.4.py
Copy-Item snapshots/agent-module-1.4.py agent.py
```

**Edit path:** replace the import section and the entire `main()` with the
two blocks below. Keep the root `.env` loader, `reply`, and entry point
unchanged. The additions to Module 1.3 are `json`, the receipt helpers,
`arepa_orders`, the store result parser, and the local `receipt` command.

<!-- build: imports -->
```python
import asyncio
import json
import os
from contextlib import AsyncExitStack
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import AnthropicFoundryClient

from receipt import OrderCapture, make_receipt
from settings import ROUTING, ToolTrace
```

<!-- build: main -->
```python
async def main() -> None:
    # 2. Keep the same configured model client.
    chat_client = AnthropicFoundryClient(
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        api_key=os.environ["FOUNDRY_API_KEY"],
        base_url=os.environ["FOUNDRY_ENDPOINT"],
    )
    # Module 1.4: keep confirmed tool data for receipt requests.
    arepa_orders = OrderCapture()

    async with AsyncExitStack() as stack:
        # 3. Capture actual order results instead of interpreting the last chat reply.
        arepa_tool = MCPStreamableHTTPTool(
            name="arepa-store",
            url=os.environ["AREPA_MCP_URL"],
            parse_tool_results=arepa_orders.parse_result,
        )
        await arepa_tool.connect()
        stack.push_async_callback(arepa_tool.close)

        # 4. Keep the second MCP connection for documented store policies.
        search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
        search_key = os.environ["AZURE_SEARCH_QUERY_KEY"]
        kb_name = quote(os.environ.get("KNOWLEDGE_BASE_NAME", "cupcake-store-kb"), safe="")
        arepa_knowledge_tool = MCPStreamableHTTPTool(
            name="arepa-knowledge-base",
            url=f"{search_endpoint}/knowledgebases/{kb_name}/mcp?api-version=2026-08-01-preview",
            header_provider=lambda _: {"api-key": search_key},
            load_prompts=False,
        )
        await arepa_knowledge_tool.connect()
        stack.push_async_callback(arepa_knowledge_tool.close)

        # 5. Combine the server-owned persona with guidance for the two tool sources.
        instructions = await arepa_tool.get_prompt("agent_instructions")
        banner = await arepa_tool.get_prompt("welcome_banner")
        instructions += ROUTING

        # 6. Trace tool names for learning without printing their arguments or results.
        arepa_agent = Agent(
            client=chat_client,
            name="arepa-agent",
            instructions=instructions,
            tools=[arepa_tool, arepa_knowledge_tool],
            middleware=[ToolTrace()],
        )
        # 7. Keep one conversation session and let the store agent greet the customer.
        arepa_session = arepa_agent.create_session()
        print(banner)
        print("Type 'exit' to quit, or 'receipt' after an order.\n")
        response = await arepa_agent.run("hello", session=arepa_session)
        print(f"Arepa Lab:\n{reply(response)}\n")

        # 8. Handle the local receipt command separately from conversational turns.
        while True:
            user_input = input("You:\n").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input:
                continue
            if user_input.lower() == "receipt":
                # Schema-valid JSON must still be backed by a successful tool result.
                if arepa_orders.source is None:
                    print("No confirmed order in this session. Place a test order first.")
                else:
                    print("Order summary, not proof of payment:")
                    print(json.dumps(make_receipt(arepa_orders.source), indent=2))
                continue
            response = await arepa_agent.run(user_input, session=arepa_session)
            print(f"\nArepa Lab:\n{reply(response)}\n")
```

### Run it

For either path, run `python agent.py` from `arepa-agent/`.

Reuse your customer ID **@lab.Variable(customerID)**. Place one **test**
order using a current voucher, then type `receipt`. If time is short,
exit and run the standalone example instead:

```powershell
python receipt.py
```

The standalone command is clearly labeled **SIMULATED TEST RESULT**. It uses
a small test-result fixture and places no order. This is the fast catch-up
path, not evidence that you ordered a Catira.

Do not make another real order. Unlike the original conversational receipt
helper, this version uses confirmed tool data so it never invents an order
ID, price, or pickup time to fill a schema.

### Verify the boundary

Check the item and kind against the successful order result or the clearly
labeled fixture. A failed order must not become a confirmed summary.

The client captures only the latest confirmed public order fields in the
current process; it does not scrape the last conversational reply or make
up missing details. A later failed ordering attempt or successful
registration/cancellation clears that captured summary. After a restart,
there is no captured result.

**Checkpoint 5.** Your summary has the required shape and matches its
source. You can explain why it is neither proof of payment nor confirmation
of an entire catering request.
