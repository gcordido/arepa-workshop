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

>[!note]When prompted to select a subscription, simply press ENTER


Then run: 

```powershell
Add-Content .env "AZURE_SEARCH_ADMIN_KEY=`"$(az search admin-key show -g @lab.CloudResourceGroup(ClaudeProject).Name --service-name search-cupcake-@lab.LabInstance.Id --query primaryKey -o tsv)`""
```

And update the existing knowledge base name:

```powershell
(Get-Content .env) -replace 'KNOWLEDGE_BASE_NAME="cupcake-store-kb"', 'KNOWLEDGE_BASE_NAME="arepa-store-kb"' | Set-Content .env
```


This effectively updates our variables so that we can create our knowledge base where the necessary documents will live to be retrieved by our agent.

### Refresh the existing store information (2 minutes)

Open the Arepa Lab store information under `/foundryiq/docs/arepalab-store-info.md`
and locate **Ordering**. Pay attention to the policies, as these will come up when the agent finally retrieves information.

Then run:

```powershell
python foundry-iq/ingest_foundry_iq.py
```

The script uploads document chunks to the `cupcake-store-kb-index`. 

Check for `Uploaded N/N chunks`. Failed uploads raise an error; if a resource
is missing or access is denied, stop and ask the instructor.

### Watch the agent choose

Let's update the agent with new functionality:

```powershell
Copy-Item agent.py agent-before-1.3.py
Copy-Item snapshots/agent-module-1.3.py agent.py
```

The knowledge base describes fictional retail policies. MCP owns live menu,
eligibility, limits, order status and pending-only cancellation. Fictional
delivery, payment, refund, deposit and cancellation policies cannot override
the counter. It accepts only single-item orders and does not collect payments
or deposits or place catering orders. Retrieved text cannot establish actual
food safety; refer suitability to staff.

Now let's run `python agent.py` from `arepa-agent/`.

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

**Checkpoint 4.** You created and uploaded documents to a Knowledge Base. Your agent selected the live store tool for availability and the KB for bulk-order policy. You checked the requirements against the source
and recognized that the notice was insufficient.
