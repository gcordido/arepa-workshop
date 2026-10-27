# Arepa Lab agent workshop

A 60-minute workshop on building and evaluating an ordering agent
with Microsoft Agent Framework, Microsoft Foundry, and MCP.

Start with [the learner introduction](lab1/intro.md). The module times total
55 minutes, with a five-minute recovery buffer. Claude is the configured
model, not the focus of the learning objectives.

## Learner package

- [Lab 1 instructions](lab1/): one page per module.
- [Agent checkpoints](arepa-agent/agent.py): `--module 1.1`, `1.2`, or `1.3`.
  Checkpoint 1.2 also supports `--tools-only`. `--trace` prints tool names
  without arguments, results, or credentials.
- [Structured summary helper](arepa-agent/receipt.py): validates the schema
  and checks values against an actual successful tool result. Its standalone
  default is a clearly labeled simulated test result.
- [Handwritten-request helper](arepa-agent/catering.py): extracts a request
  and checks it against the live menu. It never places an order.
- [Prepared extraction fallback](arepa-agent/examples/request.json): no vision
  call; explicitly labeled as pre-extracted.

The learner instructions assume a preconfigured Windows VM. They do not ask
learners to deploy infrastructure or install dependencies during the hour.

## Instructor setup

Use Python 3.11 or newer. From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

For macOS/Linux preparation, use `python3`, activate with
`source .venv/bin/activate`, and copy with `cp .env.example .env`.

Fill the root `.env` with the supplied deployment and knowledge-base values.
Never commit it. The model endpoint must stop at `/anthropic`.
Set `AREPA_MCP_URL` to the existing store endpoint. Do not copy the original
cupcake environment key or guess a knowledge-base name.

The framework core range follows the original workshop's compatibility pin;
core 1.18 changes MCP header handling. Dependencies are installed only during
VM preparation. The scripts use an explicit root `.env` path, independent
of the terminal's working directory.

Run the learner commands from `arepa-agent/`. For example:

```powershell
cd arepa-agent
python agent.py --module 1.3 --trace
```

Each process starts a fresh conversation. The `receipt` command summarizes
the latest captured confirmed order in that process, not its last chat reply.
The capture excludes internal identifiers and is cleared by failed tool
responses or later successful non-order mutations such as cancellation.
No payment is processed and no pickup time or price is fabricated.

### Required release checks

1. Supply the approved Arepa source document and the already-deployed IQ
   endpoint. Verify the pickup question against that source; a missing answer
   must be acknowledged, not replaced with old store policy.
2. Verify that policy retrieval is compatible with the store persona's scope.
   Do not override staff escalation for food-safety decisions.
3. Package an Arepa photo at `arepa-agent/images/catering-order.jpg`.
   It must match [the extraction fixture](arepa-agent/examples/request.json):
   Alex, seven Catira, Pernil crossed out for three Pelua, five Reina Pepiada,
   and `No nuts please!`. Strip photo metadata. Run the vision path and check
   the exact quantities, replacement, allergy note, and uncertainty output.
   The JSON fallback is runnable now but does not validate vision.
4. Replace the old playground/dashboard screenshots and review the deployment
   image as recorded in [the migration plan](lab1/MIGRATION-PLAN.md).
   Learner pages intentionally omit stale/broken image links until captures
   are ready; their text instructions are self-contained.
5. Rehearse on a fresh Windows learner seat. Guided content must take no more
   than 55 minutes, and the full session no more than 60. The timing is a
   target until this rehearsal is completed.

No sample policies, source documents, or replacement photos are invented by
this repository. These release checks remain necessary even though the
deployment and VM are assumed provisioned.

## Tests

After installing the requirements:

```powershell
python -m unittest discover -s tests -v
```

Tests use fixtures and mocks; they do not register customers, place or cancel
orders, consume stock, or require model credentials. Model/Foundry IQ calls,
the photo extraction, and a timed Windows rehearsal require the provisioned
workshop environment.
