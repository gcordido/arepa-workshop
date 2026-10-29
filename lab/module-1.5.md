## Module 1.5: Read and work a handwritten request (8 minutes)

A catering request arrives as a photo. It has handwritten quantities, a
crossed-out item with a replacement, and an allergy note. We will extract
and review it, not pretend that the whole request has been accepted.

### Inspect the note

Open `written_order.jpg` on the **Desktop** of your Skillable VM.
It shows an order for Eugenia, with seven Catiras, Pernil crossed out for three Peluas and
twenty-eight Reina Pepiadas, with the allergy note `No nuts please!`.
The quantities are written as numbers. Compare them yourself
before trusting extraction; the total is **38 arepas**.

![Handwritten request for Eugenia: 7 Catira, 3 Pelua replacing Pernil, 28 Reina Pepiada, and a no-nuts note.](images/written_order.jpg)

This request exceeds the retail bulk threshold. The knowledge base says
25+ arepas require 72 hours' notice and a 50% deposit. That policy does not
make the workshop counter capable of catering checkout.

### Inspect the script

Open `arepa-agent/catering.py`. It performs three steps:

1. `read_order` reads the local JPEG, encodes it as an image block, and sends
   it to the configured model. It extracts items, quantities, corrections,
   allergy notes and uncertainties into `ORDER_SCHEMA`. The prompt mentions
   tally marks, but this photo uses written numbers; verify those values.
2. `work_order` gives the request to an agent connected to the store and
   Foundry IQ. It checks the live menu, looks up allergen and bulk-order
   policy, and explains what staff must handle. Allergy suitability goes
   to staff; the agent must not infer that an item is safe.
3. The script prints a receipt for the **whole request**, labeled
   `requested`, not accepted or paid. A successful counter test, if made,
   gets its own confirmed single-item summary.

>[!warning] There is a minor bug on line 32 of the catering.py file. To fix it, replace the code in line 32 for the following `"quantity": {"type": ["integer", "null"]}`

### Run it

Exit the Module 1.4 agent by typing `exit`. You do not need to edit `agent.py` or attach the photo in the
Foundry playground.

In the VS Code PowerShell terminal, work from `arepa-agent/`. If you opened
a new terminal at the project root, run `cd arepa-agent` once.

Use the Desktop photo:

```powershell
$orderPhoto = Join-Path ([Environment]::GetFolderPath('Desktop')) 'written_order.jpg'
Test-Path -LiteralPath $orderPhoto
```

The check should print `True`. Then send the image to the model:

```powershell
python catering.py "$orderPhoto"
```


Before any store tools run, the script prints the extracted JSON and asks
`Does this extraction match the note? Type 'yes' to continue:`.
Compare the customer, all three quantities, replacement, allergy note and
any uncertainties with the photo. Type `yes` only if they match. Otherwise
type `no` to stop and ask the instructor to correct the extraction before
rerunning; do not approve incorrect JSON just to continue.

Read the policy/menu review. If time permits, explicitly authorize **one test
order**, choose a current menu item, and give your saved customer ID
**@lab.Variable(customerID)**. Provide the current dashboard voucher last.
This tests the counter flow, not food safety or acceptance of catering.
The script blocks real orders and does not expose registration or cancellation.

Type `done` to print the request receipt. You can finish without ordering.

### Check the result

- Did the image command print `Compare this extraction with the photo before using it:`?
  `PRE-EXTRACTED FALLBACK: vision was not run.` means only the fallback ran.
- Is the customer Eugenia, with quantities 7, 3, and 28 (38 total) and Pelua
  replacing Pernil rather than adding a fourth item?
- Is the allergy note verbatim, with no safety assurance?
- Did the agent retrieve the 25+ threshold, 72-hour notice, and 50% deposit?
- Did it check current menu availability rather than assume it?
- Does the full-request receipt remain labeled `requested`, with no claim
  that catering was accepted or a deposit paid?

**Checkpoint 6.** You used a handwritten request to create an order, extracted the data and checked against store policy and live tools before trying to create a matching order