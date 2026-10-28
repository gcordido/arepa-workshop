# Arepa Lab agent workshop

A 60-minute workshop on building and evaluating an ordering agent
with Microsoft Agent Framework, Microsoft Foundry, and MCP.

Start with [the learner introduction](lab/intro.md). The module times total
55 minutes, with a five-minute recovery buffer. Claude is the configured
model, not the focus of the learning objectives.

## Learner package

- [Lab instructions](lab/): one page per module.
- [Starting agent](arepa-agent/agent.py) and
  [completed snapshots](arepa-agent/snapshots/): edit progressively or copy
  a snapshot over `agent.py`. Run `python agent.py`; Modules 1.2-1.4 print
  tool names without arguments, results, or credentials.
- [Structured summary helper](arepa-agent/receipt.py): validates the schema
  and checks values against an actual successful tool result. Its standalone
  default is a clearly labeled simulated test result.
- [Handwritten-request helper](arepa-agent/catering.py): extracts a request,
  checks the live menu and store policy, and optionally places a counter
  **test** order after explicit authorization. Real orders are blocked.
- [Prepared extraction fallback](arepa-agent/examples/request.json): no vision
  call; explicitly labeled as pre-extracted.

The learner instructions assume a preconfigured Windows VM. They do not ask
learners to deploy infrastructure or install dependencies during the hour.
Module 1.3 refreshes an existing knowledge base with the Arepa source; an
instructor does this once when learner seats have query-only access.

## Hosted counter configuration

Set `AREPA_MCP_URL` to
`https://ca-arepa-mcp.yellowbeach-684b8340.eastus.azurecontainerapps.io/mcp/`.
The canonical MCP path has a trailing slash; the dashboard is the sibling
[`/dashboard`](https://ca-arepa-mcp.yellowbeach-684b8340.eastus.azurecontainerapps.io/dashboard).
The deployed slashless URL currently redirects HTTPS requests to an HTTP
location. Use HTTPS `/mcp/` directly; the server's proxy/forwarded-scheme
configuration needs an instructor deployment fix.
Keep the deployed knowledge-base identifier `cupcake-store-kb`; branding does
not require renaming Azure resources. Claude uses the configured Foundry
deployment and an endpoint ending in `/anthropic`.

The optional public workshop training key is a setup aid, not a model API
credential or an order voucher. The rotating six-character voucher comes from
the dashboard and is required for both test and real orders. Keep model
credentials and Search keys out of transcripts, screenshots and tracked files.

## Seven-tool contract

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

## Regression checks

Use a client-only virtual environment, separate from the MCP server:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

The offline suite exercises the starter, snapshots and assembled copy-paste
instructions without model credentials. See [integration checks](tests/e2e/README.md)
for isolated real-HTTP coverage and read-only hosted validation. Never run
write/lifecycle regression against the hosted workshop counter.

### Optional local GPT configuration

Workshop defaults remain Claude. The shared helpers choose
`AnthropicFoundryClient` for `/anthropic`, or `OpenAIChatClient` for
`/openai/v1`. A Foundry `/api/projects/<project>` endpoint is normalized by
appending `/openai/v1`, matching the OpenAI-compatible project API. A portal
playground URL is not an inference endpoint.

For the approved local deployment, set `FOUNDRY_MODEL_DEPLOYMENT="gpt-6-luna"`
and use that resource's endpoint and private key in an untracked local env
file. Do not copy a populated env file into the repository or change the
shared learner configuration. No Azure resource or hosted agent deployment
is needed for local execution. `AREPA_MCP_URL` still points at HTTPS `/mcp/`.

The starter, snapshots, assembled lab edits, catering agent and IQ verifier
share the same chat-client selection. Receipt and vision helpers use the
matching provider API: Claude `output_config` and image blocks, or OpenAI
strict JSON-schema `response_format` and `image_url` data URLs. Both paths
retain local schema validation, receipt/source equality, human extraction
review and the test-only catering guard. Refusals, truncation and empty
structured responses are errors; neither provider may invent an order.

Install the updated requirements in the client virtual environment, then
use `tests/e2e/hosted.py --model --env-file /approved/local/.env --output ...`
to run the actual completed Module 1.2 client. The runner reports the model
deployment and protocol so GPT evidence cannot be mistaken for a live
Claude test. The complete isolated model-driven journey is available through
`tests/e2e/run.py --suite all --env-file /approved/local/.env` with the same
server/emulator arguments documented in the integration guide.
