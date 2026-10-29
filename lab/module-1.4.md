## Module 1.4: A structured order summary (6 minutes)

The back office needs predictable JSON, but predictable JSON is not the same
as a true receipt. We will summarize a confirmed order result without fabricating a price, pickup time, or identifier.

### Read the schema and source check

Open `arepa-agent/receipt.py`. Notice that `RECEIPT_SCHEMA` requires:

- The item name from the successful tool result.
- Quantity `1`, because the counter API accepts one item per order.
- The order kind, `test` or `real`.
- Status `confirmed`.
- `payment_processed: false`.

Internal order IDs and item slugs are not included. Prices and pickup times
are omitted because this result does not establish them.

Within the file, find the API's schema configuration:

```python
output_config={"format": {"type": "json_schema", "schema": RECEIPT_SCHEMA}}
```

This is the Claude `messages.create` configuration in the shared
`structured_output` helper in `settings.py`, called by `receipt.py`.
It is not an additional edit to `agent.py`. The optional local GPT path uses
strict JSON-schema `response_format` with the same local validation.

The helper selects a text block, parses JSON, validates the schema locally,
and compares every field with the expected summary from the source result.
It raises an error if the output disagrees. Schema validity alone would not
catch the wrong item name.

### Add the receipt command

Exit the previous agent. From `arepa-agent/`, back
up your current file and copy the completed version:

```powershell
Copy-Item agent.py agent-before-1.4.py
Copy-Item snapshots/agent-module-1.4.py agent.py
```

>[!knowledge]Feel free to compare both files for changes!

### Run it

Run `python agent.py` from `arepa-agent/`.

Reuse your customer ID **@lab.Variable(customerID)**. Place one **test**
order using a current voucher, and once the order is placed then type `receipt`.

You may also place a standalone test:

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
