# Arepa Lab agent workshop

Build an arepa-ordering agent with Microsoft Foundry, Microsoft Agent Framework,
and MCP for Arepa Lab at the 2026 SHPE National Convention.
The 60-minute workshop uses Claude by default; optional GPT configuration
supports local testing with an existing Foundry deployment.

## What you will build

A Python terminal agent that keeps a conversation session, discovers live
counter tools over Streamable HTTP, and loads its persona and welcome banner
from the MCP server. You will add policy retrieval through Foundry IQ, produce
a schema-checked order summary from confirmed tool data, and review a
handwritten catering request without accepting it as a catering order.

Start with [the learner introduction](lab/intro.md). The modules total
55 minutes, with a five-minute recovery buffer:

| Module | What it adds |
|---|---|
| [1.0: Instructions and knowledge](lab/module-1.0.md) | Compare a role prompt with a grounded source of store facts. |
| [1.1: Agent and session](lab/module-1.1.md) | Run the starter and retain conversation history. |
| [1.2: Live tools](lab/module-1.2.md) | Connect the counter, retrieve its prompts, and use its menu and ordering tools. |
| [1.3: Foundry IQ](lab/module-1.3.md) | Retrieve fictional retail policies while keeping live counter rules authoritative. |
| [1.4: Structured summary](lab/module-1.4.md) | Validate JSON and compare every field with its source order result. |
| [1.5: Handwritten request](lab/module-1.5.md) | Review extraction, consult policy and availability, and optionally authorize a test order. |
| [1.6: Evaluation](lab/module-1.6.md) | Check identity reuse, menu grounding, order limits and safety boundaries. |

Microsoft Foundry hosts the model; the Python agent runs locally.
MCP (Model Context Protocol) lets it discover tools and prompts from remote
servers. No hosted agent deployment is required.

## Repository layout

```text
.
|-- lab/                         # Learner introduction, modules and screenshots
|-- arepa-agent/
|   |-- agent.py                 # Module 1.1 starter; build this up during the lab
|   |-- snapshots/               # Completed Modules 1.1-1.4 to copy over agent.py
|   |-- settings.py              # Root .env loading, provider selection and routing
|   |-- receipt.py               # Schema-checked summary; standalone example is simulated
|   |-- catering.py              # Reviewed extraction and test-only counter practice
|   |-- examples/request.json    # Pre-extracted fallback; skips vision
|   `-- requirements.txt         # Client dependencies
|-- foundry-iq/                   # Retail source, instructor ingestion and KB verifier
|-- tests/                        # Offline checks and isolated/hosted integration harnesses
|-- .env.example                  # Copy to the root .env for a fresh local setup
`-- requirements.txt             # Client and Foundry IQ dependencies
```

## Prerequisites

Workshop learners use a preconfigured Windows VM with VS Code, Python,
dependencies and a supplied root `.env`. Follow the lab pages; installing
packages and deploying infrastructure are outside the workshop hour.

For a separate local setup, you need:

- Python 3.10+ for the client, or 3.11+ to run the isolated regression suites.
- Access to an existing Foundry model deployment, its endpoint, API key and
  deployment name. Use Claude for the workshop or the optional GPT setup below.
- Access to the hosted Arepa Lab MCP counter.
- For Modules 1.3-1.6, an existing Foundry IQ knowledge base and Search query key.
  Module 1.5 uses [the included handwritten request](lab/images/written_order.jpg),
  also supplied on the Skillable VM Desktop, or the prepared JSON fallback.

Keep the client environment separate from any MCP server environment.
The [integration guide](tests/e2e/README.md) lists the additional server and
Azurite setup needed only for disposable lifecycle tests.

## Quick start

### Workshop VM

Follow [the lab](lab/intro.md) to build the agent step by step.
From the repository root, start Module 1.1 in the prepared terminal:

```powershell
cd arepa-agent
python agent.py
```

The starter has no store tools. Module 1.2 adds the MCP connection; Modules
1.3 and 1.4 add knowledge retrieval and receipts.

### Local setup and completed MCP client

For a fresh local checkout, run these Bash commands from the repository root.
If a root `.env` already exists, keep it and update only the required values
instead of copying over it.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit the root `.env` using the settings below. To run the completed Module 1.2
client without Search configuration, back up the starter and copy its snapshot:

```sh
cd arepa-agent
cp agent.py agent-before-1.2.py
cp snapshots/agent-module-1.2.py agent.py
python agent.py
```

Ask `Show today's live menu only; do not register me or place an order.`
Watch for `[tool] list_arepas`. Tool tracing prints names without arguments,
results or credentials. Type `exit` to stop.

Practice with test orders; place a real order only when explicitly intended.
For automated checks that block writes in code, use the
[hosted read-only runner](tests/e2e/README.md#hosted-read-only-suite).

## Environment variables

The application loads `.env` from the repository root independently of the
terminal's working directory. Keep populated env files local and ignored by
Git; [`.env.example`](.env.example) contains placeholders only.

| Variable | Description |
|---|---|
| `FOUNDRY_ENDPOINT` | Claude endpoint ending in `/anthropic`, or an optional GPT endpoint described below. Do not append `/v1/messages` or `/chat/completions`. |
| `FOUNDRY_API_KEY` | Private API key for the configured Foundry resource. |
| `FOUNDRY_MODEL_DEPLOYMENT` | Exact name of an existing deployment; the client does not guess it. |
| `AREPA_MCP_URL` | Set to `https://ca-arepa-mcp.yellowbeach-684b8340.eastus.azurecontainerapps.io/mcp/`. Required from Module 1.2. |
| `AZURE_SEARCH_ENDPOINT` | Existing workshop Search service URL, required for knowledge retrieval. |
| `AZURE_SEARCH_QUERY_KEY` | Query-only Search key for the agent and KB verifier, not an ingestion/admin key. |
| `KNOWLEDGE_BASE_NAME` | Keep the deployed identifier `cupcake-store-kb`; branding does not require renaming Azure resources. |

The hosted counter's dashboard is the sibling
[`/dashboard`](https://ca-arepa-mcp.yellowbeach-684b8340.eastus.azurecontainerapps.io/dashboard).
Use HTTPS `/mcp/` with the trailing slash. The deployed slashless URL currently
redirects to HTTP; its forwarded-scheme configuration still needs a server fix.

The optional public workshop training key is a setup aid, not a model API
credential or an order voucher. Both test and real orders require the current
six-character voucher displayed on the dashboard. Keep model credentials and
Search keys out of transcripts, screenshots and tracked files.

### Optional local GPT configuration

Leave shared learner settings on Claude. For your own local testing, replace
the `FOUNDRY_*` values with your existing GPT resource's endpoint, private key
and deployment name. The approved local deployment used for validation is
`gpt-6-luna`; another setup must use its own actual deployment name.

The shared helpers select `AnthropicFoundryClient` for `/anthropic` or
`OpenAIChatClient` for `/openai/v1`. A Foundry `/api/projects/<project>` endpoint
is normalized by appending `/openai/v1`. A portal playground URL is not an
inference endpoint.

Chat, receipt, vision, catering and IQ verification share this selection.
Structured helpers use Claude `output_config` and image blocks, or OpenAI
strict JSON-schema `response_format` and `image_url` data URLs. Both retain
local validation, receipt/source equality, extraction review and the test-only
catering guard. Refusals, truncation and empty structured responses are errors.

## Arepa Lab tool contract

The live counter's source of truth is `backend/mcp_server.py` and
`backend/ordering.py` in the Arepa MCP server. The client discovers these exact
tools rather than duplicating ordering rules or the server-owned persona:

| Tool | Purpose |
|---|---|
| `register_customer(first_name,last_name,city)` | Register once and retain the returned permanent customer ID. |
| `get_customer(customer_id)` | Look up a returning customer, real-order eligibility and any active real order before continuing. |
| `list_arepas()` | Current menu: `id`, `name`, `description`, numeric USD `price`, `stock_status`, `stock_label`. |
| `order_arepa(flavor_id,customer_id,kind,voucher_code)` | One item, explicitly `test` or `real`, using the current voucher. |
| `check_order_status(customer_id)` | Active real order only: pending or ready. |
| `cancel_order(customer_id,kind)` | Cancel a pending order only. |
| `voucher_status()` | Rotation timing, never a voucher code. |

Use the menu's `id` as `flavor_id`, never its display name. Keep machine item
and order IDs internal. Show every returned menu item in a numbered list with
its name, description, USD price and `stock_label`. A missing description must
be acknowledged; an empty menu cannot produce invented choices. The MCP server
owns these presentation instructions; do not add a competing client renderer.

Both kinds require a voucher. Test orders auto-complete, consume no stock and
do not appear as active real orders in `check_order_status`. Real orders
consume stock and the customer's one-real-order lifetime allowance. Cancelling
a pending real order restores both; ready orders cannot be cancelled.

The `agent_instructions` prompt owns conversation and menu presentation;
`welcome_banner` supplies the terminal banner. The standalone
`python receipt.py` example uses a clearly labeled simulated test result.
Neither it nor a schema-valid summary proves payment or catering acceptance.

### Error recovery

`found:false` means a lookup found no customer or no active real order; absence
of an active order is normal and need not have an `error_code`. `success:false`
means an action failed and must never be reported as a confirmed order.
Use stable `error_code` values for recovery, explain the returned `message`,
and follow `agent_note` privately. Never read notes or raw JSON to the learner.

| `error_code` | Recovery |
|---|---|
| `invalid_input` | Ask for every correction listed in `fields`. |
| `unknown_customer` | Recheck the existing ID; do not invent one or register repeatedly. |
| `malformed_voucher` | Impossible length/characters; explain `invalid_characters` and reread the display. This does not count toward wrong-code lockout. |
| `invalid_voucher` | Well-formed but wrong or expired; reread the current display, do not guess. The previous window remains valid for one grace window. |
| `voucher_locked` | Wait at least `retry_after_s`; do not retry during cooldown. |
| `flavor_not_found`, `sold_out` | Refresh `list_arepas` and select from the new result. |
| `active_order_exists` | Check the current real order's status before proceeding. |
| `real_limit_reached` | Offer a test order; never create another identity to evade the lifetime limit. |
| `no_active_order` | Nothing to cancel; do not claim a cancellation or refund occurred. |
| `order_not_cancellable` | The order is no longer pending; follow staff pickup instructions. |

## Knowledge-source boundary

[Store information](foundry-iq/docs/arepalab-store-info.md) is fictional retail
material for retrieval practice. MCP owns live menu, eligibility, limits,
status and pending-only cancellation. Retail delivery, payment, refund,
deposit and cancellation policies cannot override the counter or establish
food safety. Ask staff about actual ingredients, preparation and suitability.

After source changes, an instructor must approve the intended Search service,
index and KB before re-ingestion. The ingestion script updates resource
definitions and matching document IDs; it does not remove obsolete chunks.
Do not run it against shared or unrelated resources merely because credentials
are available. Keep `cupcake-store-kb` unchanged and use query-only access for
learners. See [Module 1.3](lab/module-1.3.md) for the approved refresh procedure.

## Offline checks

From the repository root, using the local client environment created above:

```sh
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

The offline suite exercises the starter, snapshots and assembled copy-paste
instructions without model credentials or live orders. It also checks both
provider paths, receipt validation, extraction review and the catering guard.

## Client-to-MCP integration checks

The [integration guide](tests/e2e/README.md) covers disposable real-HTTP
contract/lifecycle tests, an actual model-driven client journey, and read-only
checks against the hosted counter. It includes the full server/emulator
arguments for `tests/e2e/run.py --suite contract` or `--suite all`.

To check the hosted counter with the actual completed Module 1.2 client and
your configured model, run from the repository root:

```sh
.venv/bin/python tests/e2e/hosted.py --model --output .venv/hosted-results.json
```

Omit `--model` for discovery, menu and voucher timing without model calls.
Use `--env-file /approved/local/.env` for an alternate model configuration.
The hosted adapter exposes only `list_arepas` and `voucher_status` and blocks
other calls before transport. The known slashless redirect still produces a
failed check even when the canonical connection and menu conversation pass.
Never run write/lifecycle regression against the hosted workshop counter.

Results identify the actual model deployment and protocol. Live GPT evidence
does not establish a live Claude pass. Live Claude execution, IQ retrieval,
real-photo extraction and the combined catering flow still need appropriate
configuration and validation. The photo is included at
[`lab/images/written_order.jpg`](lab/images/written_order.jpg); its presence
alone does not establish a successful live extraction.

## Troubleshooting

| Symptom | Check |
|---|---|
| Missing module or import | Use the prepared VM environment, or activate your local venv and install the root `requirements.txt`. Keep server dependencies separate. |
| Missing setting or placeholder error | Edit the root `.env`, not one under `arepa-agent/`, and replace the required placeholders. |
| Model 401/403 or `DeploymentNotFound` | Confirm the resource's key, endpoint and exact deployment name. Ask the instructor on the workshop VM. |
| Model endpoint 404 | Use `/anthropic` for Claude or a supported GPT endpoint; do not append the request API path yourself. |
| MCP redirect or connection failure | Use the confirmed HTTPS `/mcp/` URL with its trailing slash. |
| Knowledge connection fails | Check the existing Search endpoint, query key and `cupcake-store-kb`; Module 1.2 can run without IQ. Do not run ingestion as a connection fix. |
| Voucher, stock or order rejection | Follow [error recovery](#error-recovery); do not guess codes or register a new identity to evade limits. |
| `receipt` says no confirmed order | Capture exists only in the current process and clears after failed actions or successful registration/cancellation. Use a test order or the labeled simulated standalone example in [Module 1.4](lab/module-1.4.md). |
| Catering photo missing | Follow [Module 1.5](lab/module-1.5.md) to use the Skillable VM Desktop photo, or run `python catering.py "../lab/images/written_order.jpg"` from `arepa-agent/`. Use `python catering.py --extracted examples/request.json` only for the explicit catch-up path; it does not validate vision. |
