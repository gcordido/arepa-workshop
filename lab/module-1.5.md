## Module 1.5: Read a handwritten request (8 minutes)

A customer brings a handwritten Arepa request. It has tally quantities, a
crossed-out item with a replacement, and an allergy note. We will extract
and review it, not pretend that the whole request has been accepted.

### Inspect the note first

Open the instructor-supplied `arepa-agent/images/catering-order.jpg`.
Read its names, quantities, correction, and allergy note yourself.
The Arepa version must match the prepared extraction example:

- Customer: Alex.
- Catira: seven tally marks.
- Pernil crossed out and replaced with Pelua: three tally marks.
- Reina Pepiada: five tally marks.
- Allergy note: `No nuts please!`

Do not use the old cupcake photo. If the replacement photo is not supplied,
use the explicitly labeled pre-extracted fallback below; that path does not
demonstrate vision.

### Inspect the pipeline

Open `arepa-agent/catering.py`:

1. `read_order` sends the photo as an image block with `ORDER_SCHEMA`.
   The extraction records items, corrections, allergy notes, and uncertainties.
2. `current_menu` calls **only** `list_arepas` through a read-only client path.
3. `review_request` compares the extracted names with the live menu and
   explains the order boundary.

The script has no registration, ordering, or cancellation path. No customer
ID or voucher is needed, and it cannot consume your real-order allowance.

### Run it

From `arepa-agent/`, with the prepared photo:

```powershell
python catering.py images/catering-order.jpg
```

If the photo is unavailable, or the instructor directs you to the catch-up
path:

```powershell
python catering.py --extracted examples/request.json
```

The fallback validates and reviews prepared JSON against the live menu. It
does not call the vision model; record the vision checkpoint as not exercised.

### Check extraction and judgment separately

- Are the quantities 7, 3, and 5?
- Is Pernil removed and Pelua substituted?
- Is the allergy note copied exactly?
- Are illegible details reported as uncertainties rather than guessed?
- Do the item names appear on the **current** menu? Availability can change.
- Does the output clearly say that nothing has been ordered or reserved?

An available menu name does not establish allergen safety. Ask staff about
the allergy note; the script must not identify an item as safe. The counter
accepts one item per order, not a multi-item catering checkout. Do not infer
notice periods, deposits, or catering service from this request.

**Checkpoint 6.** You reviewed an extracted request against its source and
the live menu, or explicitly used the pre-extracted fallback. In either
case, no unconfirmed request became an order or a payment receipt.

<!-- Asset pending: prepare the Arepa handwritten photo described above,
strip metadata, and rehearse extraction before the learner VM is released. -->
