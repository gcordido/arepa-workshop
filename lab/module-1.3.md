## Module 1.3: Ground answers in store knowledge (8 minutes)

The store tools answer questions about current menu, customers, and orders.
They are not a general policy-document search. The store's approved
information is in a separately provisioned **Foundry IQ** knowledge base.

Foundry IQ is a managed knowledge layer built on Azure AI Search. Its MCP
endpoint gives this agent a second source of tools.

### Inspect the second connection

The root `.env` already contains:

```dotenv
AZURE_SEARCH_ENDPOINT="https://<service>.search.windows.net"
AZURE_SEARCH_QUERY_KEY="<provided-query-key>"
KNOWLEDGE_BASE_NAME="<provided-arepa-knowledge-base-name>"
```

Use the supplied values. A knowledge-base name is a deployed identifier,
not a label you can rename only in code.

In `agent.py`, find the checkpoint 1.3 block:

```python
knowledge = MCPStreamableHTTPTool(
    name="arepa-knowledge-base",
    url=f"{search_endpoint}/knowledgebases/{kb}/mcp?api-version=2026-08-01-preview",
    header_provider=lambda _: {"api-key": search_key},
    load_prompts=False,
)
```

The agent now receives both tool connections. Read `ROUTING` near the top
of the file: live operations go to the store; documented information goes
to the knowledge base. Neither source authorizes extra real orders, bulk
checkout, or payments.

### Watch the agent choose

Type `exit` in the previous agent, then run:

```powershell
python agent.py --module 1.3 --trace
```

Use your existing customer ID **@lab.Variable(customerID)** if asked.
Do not register again.

Ask two questions:

1. `What arepas are available now? Please show the current menu.`
2. `What does the store information say about pickup? Look it up in the knowledge base.`

For question 1, look for `list_arepas`. For question 2, look for a retrieval
tool from the knowledge-base connection. Tool names can vary with its
configuration; inspect the `[tool]` lines rather than judging by fluent prose.

Compare the second answer with the approved Arepa source document supplied
by your instructor. If the document has no pickup information, the correct
result is to say it is not documented and refer you to staff. It is not
permission to invent hours, deposits, or delivery rules.

Do not use an allergy question to prove general policy retrieval. The store
requires staff escalation for food-safety and dietary-suitability decisions,
even when an approved document contains ingredient or allergen information.

**Checkpoint 4.** You identified which tool source served each question
and checked a retrieved answer against its document, or recognized a
documented-information gap. Retrieval does not guarantee every answer exists.

If the knowledge connection fails, keep the error visible and ask your
instructor to check the supplied endpoint, query key, and KB name. Do not
silently continue as though the answer had been grounded.
