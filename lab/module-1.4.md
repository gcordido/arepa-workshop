## Module 1.4: A structured order summary (6 minutes)

The back office needs predictable JSON, but predictable JSON is not the same
as a true receipt. This demo does not process payments. We will summarize a
confirmed order result without inventing a price, pickup time, or identifier.

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

The helper selects a text block, parses JSON, validates the schema locally,
and compares every field with the expected summary from the source result.
It raises an error if the output disagrees. Schema validity alone would not
catch the wrong item name.

### Run it

If you still have an agent process with a confirmed order in memory, type:

```text
receipt
```

Otherwise run this from `arepa-agent/`:

```powershell
python receipt.py
```

The standalone command is clearly labeled **SIMULATED TEST RESULT**. It uses
a small test-result fixture and places no order. This is the fast catch-up
path, not evidence that you ordered a Catira.

To try a live summary after restarting the agent, make at most one **test**
order using your saved ID and current voucher, then type `receipt`.
Do not make another real order.

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
