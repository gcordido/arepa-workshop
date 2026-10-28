# Integration checks

The harness adapts the previous `code-with-foundry-shpe-workshop` offline and
real-HTTP regressions (alignment commits `87858a5`, `82b5467`, `9afb98d`) for
this starter, snapshots, receipt helper and catering guard.

## Disposable lifecycle suite

Install the client dependencies from `tests/requirements.txt` in `.venv`.
Prepare a **different** server virtual environment from the reference server's
`requirements.txt`. Install Azurite only for local testing:

```sh
python3 -m venv .venv/server
.venv/server/bin/python -m pip install -r /path/to/arepa-mcp/requirements.txt
npm install --prefix .venv/azurite azurite
.venv/bin/python tests/e2e/run.py --suite contract \
  --server-repo /path/to/arepa-mcp \
  --server-python .venv/server/bin/python \
  --azurite .venv/azurite/node_modules/.bin/azurite-table \
  --artifacts /path/to/session-files/isolated-results
```

The reference checkout is read-only. The harness copies only `backend/` into a
temporary directory, excludes env files, uses a clean server environment with
fresh local secrets, and starts Azurite on a loopback-only random port.
Synthetic customers and inventory never reach Azure. Process cleanup runs even
on test failure; temporary code and storage are discarded. Logs and a summary
remain in the selected artifact directory. Never point lifecycle tests at the
hosted counter, reuse production storage credentials or run the server from the
primary checkout.

The suite covers discovery, both prompts, exact seven-tool schemas, every tool,
input errors, malformed and expired vouchers, lockout/cooldown hints, voucher
grace, stock thresholds, test auto-completion, pending cancellation with stock
and allowance restoration, readiness, collection and lifetime limits.

Use `--suite all --env-file /approved/local/.env` to add an actual model-driven
journey through the completed Module 1.2 client. The model uses the configured
provider; all registration, voucher errors, orders and cancellation remain
inside the disposable server and emulator. A model conversation pass is
reported separately from deterministic contract tests.

## Hosted read-only suite

```sh
.venv/bin/python tests/e2e/hosted.py --output /path/to/session-files/hosted.json
.venv/bin/python tests/e2e/hosted.py --model --output /path/to/session-files/hosted-model.json
```

The default checks the confirmed hosted URL, redirect/canonical path, tool
and prompt discovery, live menu fields and voucher timing using the real MCP
adapter. `--model` additionally runs the actual Module 1.2 client with the configured model
and its server-owned prompt, observing tool calls and checking every menu item
in the reply. Model calls require approved `FOUNDRY_*` settings in the root
`.env` or process environment. An alternate configuration file can be selected
with `--env-file`; credentials are never included in results. The endpoint must
identify `/anthropic`, `/openai/v1` or a Foundry `/api/projects/<project>`.
A missing or incompatible configuration is a blocked check.
No hosted agent deployment is needed: the existing Python agent runs locally.
Results identify the actual deployment/protocol. GPT evidence does not
establish a live Claude pass. This menu-only check does not validate live
receipt, vision or knowledge-base retrieval calls.

The hosted adapter exposes only `list_arepas` and `voucher_status` to the model
and rejects all other tool calls before transport. It never registers a
customer, orders, submits a voucher, cancels, or writes Search. Missing model
configuration is a blocked check, never a pass. Missing descriptions must be
acknowledged, prices must be USD, machine item IDs must stay private, and an
empty menu cannot produce invented numbered choices. Presentation remains the
server's responsibility; report deployment prompt mismatches rather than
adding a client-side persona or renderer.
