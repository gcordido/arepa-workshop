## Module 1.3: Ground answers in store knowledge (8 minutes)

The store tools answer questions about current menu, customers, and orders.
They are not a general policy-document search. A **Foundry IQ** knowledge
base already exists; you will refresh its store information with the Arepa
document, then connect your agent.

Foundry IQ is a managed knowledge layer built on Azure AI Search. Its MCP
endpoint gives this agent a second source of tools.

### Updating our environment variables

Type `exit` in any running agent.Log in by running the following command from the root path:

```powershell
az login --use-device-code
```

Then run: 

```powershell
Add-Content .env "AZURE_SEARCH_ADMIN_KEY=`"$(az search admin-key show -g @lab.CloudResourceGroup(ClaudeProject).Name --service-name search-cupcake-@lab.LabInstance.Id --query primaryKey -o tsv)`""
```

This effectively updates our variables so that we can create our knowledge base where the necessary documents will live to be retrieved by our agent.

### Refresh the existing store information (2 minutes)

Open the Arepa Lab store information under `/foundryiq/docs/arepalab-store-info.md`
and locate **Ordering**. Pay attention to the policies, as these will come up when the agent finally retrieves information.

Then run:

```powershell
python foundry-iq/ingest_foundry_iq.py
```

The script only uploads document chunks to the existing `cupcake-store-kb-index`.
It does not create resources, change the index schema (including the `id`
field), or update the knowledge source or KB configuration. All resources
must already exist.

Check for `Uploaded N/N chunks`. Failed uploads raise an error; if a resource
is missing or access is denied, stop and ask the instructor.

### Inspect the second connection

The root `.env` already contains:

```dotenv
AZURE_SEARCH_ENDPOINT="https://<service>.search.windows.net"
AZURE_SEARCH_QUERY_KEY="<provided-query-key>"
KNOWLEDGE_BASE_NAME="cupcake-store-kb"
```

Use the supplied values. A knowledge-base name is a deployed identifier,
not a label you can rename only in code. All Azure resource names keep the
original cupcake naming; Python variables and tool aliases use arepas.

**Edit path:** replace the import section with this block, then replace the
entire `main()` with the next block. Keep the root `.env` loader, `reply`,
and entry point from Module 1.1 unchanged. This adds URL escaping and
`ROUTING` to the Module 1.2 imports.

<!-- build: imports -->
```python
import asyncio
import os
from contextlib import AsyncExitStack
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

from agent_framework import Agent, MCPStreamableHTTPTool
from settings import ROUTING, ToolTrace, create_chat_client
```

Section **4** adds the knowledge connection, **5** appends the routing
guidance from `settings.py`, and **6** gives the agent both tool servers.

<!-- build: main -->
```python
async def main() -> None:
    # 2. Keep the same configured model client.
    chat_client = create_chat_client()

    # 3. Discover the store tools; close connected servers on exit or error.
    async with AsyncExitStack() as stack:
        arepa_tool = MCPStreamableHTTPTool(
            name="arepa-store",
            url=os.environ["AREPA_MCP_URL"],
        )
        await arepa_tool.connect()
        stack.push_async_callback(arepa_tool.close)

        # 4. Add policy retrieval using a read-only Search query key.
        search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
        search_key = os.environ["AZURE_SEARCH_QUERY_KEY"]
        # Keep the existing Azure resource name, escaped as a URL path segment.
        kb_name = quote(os.environ.get("KNOWLEDGE_BASE_NAME", "cupcake-store-kb"), safe="")
        arepa_knowledge_tool = MCPStreamableHTTPTool(
            name="arepa-knowledge-base",
            url=f"{search_endpoint}/knowledgebases/{kb_name}/mcp?api-version=2026-08-01-preview",
            header_provider=lambda _: {"api-key": search_key},
            load_prompts=False,
        )
        await arepa_knowledge_tool.connect()
        stack.push_async_callback(arepa_knowledge_tool.close)

        # 5. Combine the store persona with guidance for the two tool sources.
        instructions = await arepa_tool.get_prompt("agent_instructions")
        banner = await arepa_tool.get_prompt("welcome_banner")
        instructions += ROUTING

        # 6. Both servers are available; the agent selects tools per question.
        arepa_agent = Agent(
            client=chat_client,
            name="arepa-agent",
            instructions=instructions,
            tools=[arepa_tool, arepa_knowledge_tool],
            middleware=[ToolTrace()],
        )

        # 7. Keep one session and let the agent greet the customer first.
        arepa_session = arepa_agent.create_session()
        print(banner)
        print("Type 'exit' to quit.\n")
        response = await arepa_agent.run("hello", session=arepa_session)
        print(f"Arepa Lab:\n{reply(response)}\n")

        # 8. Both tool servers remain available throughout the conversation.
        while True:
            user_input = input("You:\n").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input:
                continue
            response = await arepa_agent.run(user_input, session=arepa_session)
            print(f"\nArepa Lab:\n{reply(response)}\n")
```

The knowledge base describes fictional retail policies. MCP owns live menu,
eligibility, limits, order status and pending-only cancellation. Fictional
delivery, payment, refund, deposit and cancellation policies cannot override
the counter. It accepts only single-item orders and does not collect payments
or deposits or place catering orders. Retrieved text cannot establish actual
food safety; refer suitability to staff.

### Watch the agent choose

**Fast path:** if you did not make the edits above, back up your file and
copy the completed snapshot:

```powershell
Copy-Item agent.py agent-before-1.3.py
Copy-Item snapshots/agent-module-1.3.py agent.py
```

For either path, run `python agent.py` from `arepa-agent/`.

Use your existing customer ID **@lab.Variable(customerID)** if asked.
Do not register again.

Ask two questions:

1. `What arepas are available now? Please show the current menu.`
2. `I need 30 arepas for an event in two days. What are the ordering requirements?`

For question 1, look for `list_arepas`. For question 2, look for a retrieval
tool from the knowledge-base connection. Tool names can vary with its
configuration; inspect the `[tool]` lines rather than judging by fluent prose.
Neither question names a tool: the agent should choose using its instructions
and tool descriptions.

Open [the Arepa Lab store information](../foundry-iq/docs/arepalab-store-info.md)
and compare the second answer with **Ordering**:

- **25 or more arepas** is a bulk order.
- Bulk orders require **72 hours' notice** and a **50% deposit**.
- Two days is **48 hours**, so the requested timing does not meet the policy.

The agent should explain the requirements without claiming to have accepted
the catering order or collected a deposit. No voucher or order placement is
needed for these two questions.

Do not use an allergy question to prove general policy retrieval. The store
requires staff escalation for food-safety and dietary-suitability decisions,
even when an approved document contains ingredient or allergen information.

**Checkpoint 4.** You refreshed the existing KB, or followed the instructor's
shared refresh, without creating new resources. Your agent selected the
live store tool for availability and the KB for bulk-order policy. Verify
that retrieved source content refers to Arepa Lab and arepas, not the old
cupcake store: the policy numbers alone are unchanged and cannot prove that
the refresh worked. You checked the requirements against the new source
and recognized that the notice was insufficient.

If the knowledge connection fails, keep the error visible and ask your
instructor to check the supplied endpoint, query key, and KB name. Do not
silently continue as though the answer had been grounded.
