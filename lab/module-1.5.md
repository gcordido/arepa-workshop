## Module 1.5: Read and work a handwritten request (8 minutes)

A catering request arrives as a photo. It has tally quantities, a
crossed-out item with a replacement, and an allergy note. We will extract
and review it, not pretend that the whole request has been accepted.

### Inspect the note

Open the instructor-supplied `arepa-agent/images/catering-order.jpg`.
It should show Eugenia, seven Catira, Pernil crossed out for three Pelua,
twenty-eight Reina Pepiada, and the margin note `No nuts please!`.
Quantities are tally marks; compare them yourself before trusting extraction.

This request exceeds the retail bulk threshold. The knowledge base says
25+ arepas require 72 hours' notice and a 50% deposit. That policy does not
make the workshop counter capable of catering checkout.

### Inspect the script

Open `arepa-agent/catering.py`. It performs three steps:

1. `read_order` extracts items, quantities, corrections, allergy notes and
   uncertainties into `ORDER_SCHEMA`.
2. `work_order` gives the request to an agent connected to the store and
   Foundry IQ. It checks the live menu, looks up allergen and bulk-order
   policy, and explains what staff must handle. Allergy suitability goes
   to staff; the agent must not infer that an item is safe.
3. The script prints a receipt for the **whole request**, labeled
   `requested`, not accepted or paid. A successful counter test, if made,
   gets its own confirmed single-item summary.

### Run it

From `arepa-agent/`:

```powershell
python catering.py images/catering-order.jpg
```

If the replacement photo is not ready, the catch-up path uses prepared
JSON and explicitly skips vision:

```powershell
python catering.py --extracted examples/request.json
```

Compare the extraction with the note, then type `yes` to continue only if it
matches. Otherwise stop and ask the instructor to correct it.

Read the policy/menu review. If time permits, explicitly authorize **one test
order**, choose a current menu item, and give your saved customer ID
**@lab.Variable(customerID)**. Provide the current dashboard voucher last.
This tests the counter flow, not food safety or acceptance of catering.
The script blocks real orders and does not expose registration or cancellation.

Type `done` to print the request receipt. You can finish without ordering.

### Check the result

- Are the quantities 7, 3, and 28, with Pelua replacing Pernil?
- Is the allergy note verbatim, with no safety assurance?
- Did the agent retrieve the 25+ threshold, 72-hour notice, and 50% deposit?
- Did it check current menu availability rather than assume it?
- Does the full-request receipt remain labeled `requested`, with no claim
  that catering was accepted or a deposit paid?

**Checkpoint 6.** A handwritten request was extracted and checked against
store policy and live tools. Any single-item test order is distinct from
the unconfirmed catering request. The JSON fallback does not validate vision.
