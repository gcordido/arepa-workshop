# Lab 1 migration plan: Arepa Lab agents

## Goal and scope

Update Lab 1 from Sparkles Cupcakes to Arepa Lab, with the learning objectives
centered on building an agent: instructions, sessions, tools, grounding,
structured outputs, multimodal input, and evaluation.

- Keep Microsoft Foundry, Microsoft Agent Framework, Python, the Skillable
  Windows VM, PowerShell, and all existing Skillable credential and customer-ID
  placeholders.
- Assume the VM, dependencies, model deployment, Foundry IQ knowledge base,
  configuration, and completed-code snapshots are provisioned equivalently to
  the original workshop. This is not a deployment or infrastructure project.
- Keep Claude as the configured model. Retain the actual client imports,
  Anthropic endpoint shape, and API parameters where technically required.
  Remove provider marketing, model-tier prerequisites, and provider-specific
  learning outcomes. Agent-first wording does not make the SDK provider-neutral.
- Use the already-running Arepa Lab MCP:
  `https://ca-arepa-mcp.yellowbeach-684b8340.eastus.azurecontainerapps.io/mcp/`.
- Replace the required model-tier comparison with agent-reliability evaluation
  using the same configured deployment throughout.
- Target **55 minutes of guided work plus 5 minutes of buffer**, with a hard
  workshop limit of 60 minutes.
- Do not modify the sibling source repository or the running MCP during this
  documentation migration. Record conflicts requiring coordination instead.

This file is the plan only; the learner instructions have not yet been changed.

## Evidence and assumptions

Reviewed all eight pages in this folder and the original assets and supporting
code in [the sibling workshop](../../model-mastery/anthropic/):

- [Original Skillable image inventory](../../model-mastery/anthropic/skillable/images/README.md)
- [Agent and completed snapshots](../../model-mastery/anthropic/sparkles-agent/)
- [Receipt implementation](../../model-mastery/anthropic/sparkles-agent/receipt.py)
- [Catering implementation](../../model-mastery/anthropic/sparkles-agent/catering.py)
- [Original policy document](../../model-mastery/anthropic/foundry-iq/docs/cupcake-store-info.md)
- [Catering image guidance](../../model-mastery/anthropic/sparkles-agent/images/README.md)

Read-only inspection of the supplied endpoint confirmed server name
`Arepa Lab`, version `3.4.7`, seven tools, and the `agent_instructions` and
`welcome_banner` prompts. Retrieving `agent_instructions` works. The server
currently lists no resources; this does not imply the separately provisioned
Foundry IQ endpoint is missing.

The current menu contains Catira, Domino, Pabellon, Pelua, Pernil, Reina Pepiada,
and Viuda. Observed prices are USD 2.00, 3.50, and 5.00 depending on the item.
Names, availability, and prices are live data, not permanent lab fixtures.

No customers were registered, orders created or cancelled, or stock changed
during planning. The deployed knowledge base, learner VM, and agent scripts
were not executed or independently verified; provisioning parity is assumed
as requested.

## Module-by-module changes and time budget

| Page | New focus | Minutes | Planned changes |
|---|---|---:|---|
| [Introduction](intro.md) | Build an Arepa Lab ordering agent | Included in 1.0 | Replace the Sparkles story and provider-led outcomes. Explain what belongs to the agent versus its model. State the 60-minute limit and the module dependency/shortcut paths. |
| [1.0](module-1.0.md) | Instructions are not store knowledge | 5 | Keep VM and Foundry sign-in. Open the single configured deployment, not two tiers. Use a short Arepa Lab role prompt and one menu or policy question to show that an ungrounded response is not evidence. Do not promise that the model will always hallucinate. |
| [1.1](module-1.1.md) | An agent, a client, and a session | 7 | Keep environment checks and endpoint troubleshooting. Use the provisioned Arepa agent path/name consistently. Explain the client as configuration, the agent as behavior/tools, and the session as conversation history. Run one short exchange. |
| [1.2](module-1.2.md) | Live tools and a server-managed persona | 12 | Retain tools-first, then persona. Use the Arepa MCP URL and tool names. Demonstrate a live menu, fetch both existing prompts, and complete registration or returning-customer lookup. Save the customer ID. Make one explicit test-or-real order; only a real order is collected. Show the Arepa dashboard. |
| [1.3](module-1.3.md) | Grounded answers and tool selection | 8 | Keep Foundry IQ and the second MCP connection. Replace store names, document/KB references, routing instructions, and policy questions with the deployed Arepa equivalents. Use one store-data question and one approved FAQ question. Do not carry over cupcake policies by substitution. |
| [1.4](module-1.4.md) | Structured order summaries | 6 | Keep a schema example and a short run. Use actual order/menu data, not guessed prices or generated IDs. Distinguish schema validity from factual validity, order success, and payment. Resolve the receipt/MCP privacy conflict before finalizing learner-visible fields. |
| [1.5](module-1.5.md) | Read and validate a handwritten request | 8 | Use a replacement Arepa note and the provisioned script. Inspect extraction, tally quantities, and the crossed-out correction. Validate requests against the menu and approved policy. Do not describe a full catering request as placed, or promise allergen safety. A test order, if appropriate, remains one item and requires a voucher. |
| [1.6](module-1.6.md) | Evaluate agent reliability | 9 | Replace the Sonnet/Haiku exercise with a compact scenario checklist on the same deployment. Check tool grounding, returning-customer handling, missing-input clarification, and correct test/real behavior. Use a fresh session where appropriate. Include a short wrap-up, without assuming an afternoon Lab 2. |
| Buffer | Sign-in, voucher refresh, and recovery | 5 | Use completed checkpoints instead of letting setup or typing overrun the workshop. |
| **Total** | | **60** | **55 minutes guided content + 5 minutes buffer.** |

### Keeping the workshop within one hour

- Preserve the progressive build, but make completed snapshots the fast path.
  Provide one copy/run action per checkpoint; keep full code as a reference,
  not something learners must retype.
- Keep the initial sign-in path concise and use the prefilled environment.
- Reduce Module 1.3 from four questions to two. Use the policy scenario again
  in 1.6 rather than introducing a second long exercise.
- Keep 1.4 to one schema inspection and one output check.
- Give 1.5 a prepared image and script. No image creation or catering-code
  typing during the lab.
- In 1.6, use short scenarios and a shared rubric instead of two long model
  runs and a tier discussion. No second deployment is required.
- Define snapshot starting points precisely: 1.4 needs a completed agent
  checkpoint; 1.5 needs its prepared dependencies; 1.6 needs the grounded
  agent. Replace the misleading blanket claim that 1.4-1.6 are independent.
- Time a complete rehearsal in a fresh Skillable VM, including registration,
  voucher entry, image inspection, and switching between portal and terminal.
  If it exceeds 55 minutes before buffer, shorten repetitions or move
  explanatory code to reference material rather than rushing the learner.

## MCP compatibility and conflict register

These are observable differences or conflicts between the running Arepa MCP
contract and the current cupcake instructions/supporting code. They need
explicit resolution; renaming the shop is not sufficient.

| Area | Current expectation | Arepa MCP contract / conflict | Planned resolution |
|---|---|---|---|
| Tool names | Cupcake-store tools and examples | `register_customer`, `get_customer`, `list_arepas`, `order_arepa`, `check_order_status`, `cancel_order`, `voucher_status` | Update tool descriptions, examples, and any code that directly names tools. Framework discovery still works without hand-written wrappers. |
| Configuration and paths | `CUPCAKE_MCP_URL`, `cupcake-store`, `cupcake-agent`, `sparkles-agent/`, `cupcake-store-kb` | Endpoint and store identity have changed; the VM's actual renamed paths/settings still need to be matched | Proposed convention: `AREPA_MCP_URL`, `arepa-store`, `arepa-agent`, `arepa-agent/`, `arepa-store-kb`. Coordinate with the VM package; do not rename a deployed KB or environment variable only in prose. |
| Prompts | `agent_instructions` and `welcome_banner` | Both names remain available; persona already enforces the Arepa flow | Keep prompt retrieval. Avoid local instructions that contradict the server persona. |
| Registration | Copy an eight-character ID after ordering | Collect first name, last name, and city before registration; returning customers must be looked up before menu/voucher steps | Explain new versus returning flow. Save the returned ID immediately; reuse it through later modules. Do not mint IDs to bypass the real-order cap. |
| Menu and stock | Cupcake flavors, hazelnut sold out, raw assumptions about alternatives | Menu has item IDs, display names, descriptions, USD prices, and qualitative stock labels; availability changes | Show names and stock labels; pass the returned ID as `flavor_id` internally. Do not assert a specific item is sold out unless the workshop fixture guarantees it. |
| Pricing | Receipt code defaults to 400 cents per cupcake | Arepa prices differ by item; demo processes no payments | Use tool-sourced prices. Label outputs as demo order summaries, not evidence of payment. Preserve missing data as unavailable rather than fabricating it. |
| Quantity and order kind | Order a cupcake; later produce a receipt for a multi-item catering request | `order_arepa` orders one item, has no quantity parameter, and requires explicit `kind="test"` or `"real"` | Do not imply bulk checkout exists. Separate a requested catering estimate from an accepted single-item order. Ask order kind before voucher entry. |
| Lifetime limit | Later modules ask learners to place further orders | One real arepa per customer; test orders are unlimited, voucher-backed, and do not consume stock | Reserve real pickup for 1.2 if desired; use test orders for subsequent exercises. Do not cancel or re-register just to bypass the cap. |
| Voucher | Read a rotating code from the dashboard | Six-character voucher required for both order kinds; obtain it last. Invalid codes and lockouts have explicit recovery responses | Use a fresh on-screen code, never a fixed sample presented as valid. Teach clarification and retry timing; do not brute-force codes during evaluation. |
| Dashboard and status | Ready means collect an order | Real orders have active pending/ready status; test orders auto-complete and are not tracked by `check_order_status` | Separate real pickup from the test feed. Avoid polling test orders or promising food for them. |
| Cancellation | Not explicitly taught | Only pending orders can be cancelled; ready orders cannot. Cancelling a real order restores its stock/cap | Document only as a recovery path or evaluation discussion, not a way to generate additional real orders for practice. |
| Policy knowledge | Cupcake hours, shipping, refunds, loyalty, 72-hour notice, 50% deposit, and 25-item threshold | Store MCP has no policy lookup tool. Separate Arepa IQ content is assumed deployed, but those cupcake rules are not verified Arepa policies | Match the approved Arepa source and KB. List actual policy facts before writing expected answers. Do not assume nationwide shipping or bakery rules apply to the convention demo. |
| Food safety | Knowledge lookup leads to a "safe" test order; tree-nut policy treated as sufficient | Persona directs food-safety questions to staff and forbids inferred allergen/dietary suitability | Remove "safe order" claims. Agree whether IQ may quote approved safety information while still referring suitability decisions to staff. Never override this boundary silently. |
| Scope of conversation | Catering and policy advice are expected agent behavior | Persona is restricted to arepas, ordering, and status; a strict reading may reject broader store-policy/catering requests | Confirm approved FAQ/catering scope and align server persona with local IQ routing. Otherwise teach escalation and request extraction, not successful catering handling. |
| Receipt identifiers | Schema requires `order_id`; helper fabricates `SPK-####` when absent | Persona does not allow exposing internal order IDs or flavor slugs in conversational output | Decide whether a separate authorized back-office output may include actual IDs, or revise learner-visible schema to omit them. Never invent IDs to satisfy a schema. |
| Receipt grounding | Receipt uses the agent's last reply; catering receipt covers every requested item | Last reply may not contain the accepted order; a request is not an accepted order, and pickup time is not guaranteed | Use an explicit confirmed-order source for summaries. Keep extracted request/estimate separate, with no fabricated acceptance, pickup time, or totals. Update helper/snapshots with the documentation. |
| Error handling | Mostly happy-path ordering | Tools return structured failures, sometimes `found: false`, with recovery guidance | Explain user-facing recovery without dumping raw tool JSON or internal notes. Never show a success receipt after a failed order. |
| Tier comparison | Two Claude deployments and fixed hazelnut/red-velvet scenario | Model comparison is no longer a workshop objective; original products/policies do not match | Remove Haiku setup, switching commands, and model-tier scoring. Evaluate the agent against the current tool and policy contracts. |

### Coordination gates before the rewrite is finalized

1. Confirm the VM's agent folder, environment key, snapshot names, Arepa policy
   document path, and deployed knowledge-base name. Deployment parity does not
   tell us their literal names.
2. Obtain the approved Arepa FAQ facts. Resolve policy/catering scope and
   food-safety escalation against the server persona; do not broaden safety
   advice merely to preserve a cupcake exercise.
3. Agree on the user-visible summary schema and the source of confirmed order
   data. This may require changing the packaged receipt helper, not just text.
4. Choose stable workshop examples from the actual menu and prepare the
   matching handwritten note. Guarantee a sold-out fixture only if staff
   explicitly configure one; otherwise evaluate unavailability conditionally.

## Image audit and replacement checklist

The current Lab 1 pages link to `../images/...`, but this workspace has no
root-level image folder. Packaging must supply those assets at the expected
paths. The original source has duplicate screenshot sets in
`anthropic/skillable/images/` and `anthropic/standalone/images/`; use the
Skillable set as this lab's source and avoid creating unnecessary duplicate
sets here.

All six Lab 1 image assets below were visually inspected in the sibling repo.

| Original asset | Used by | Decision | Capture/replacement requirements |
|---|---|---|---|
| [01-foundry-home.png](../../model-mastery/anthropic/skillable/images/01-foundry-home.png) | 1.0 | **Reuse if navigation still matches** | No Sparkles content. Recapture only for portal/VM differences. Explain that this is navigation, not a model-comparison exercise. |
| [02-deployments.png](../../model-mastery/anthropic/skillable/images/02-deployments.png) | 1.0 | **Prefer a simplified recapture/crop** | Original shows Sonnet, Opus, and Haiku, reinforcing the removed tier objective. Highlight only the configured workshop deployment. A visible Claude model name is fine. |
| [03-playground.png](../../model-mastery/anthropic/skillable/images/03-playground.png) | 1.0 | **Replace** | Original instructions and response explicitly mention Sparkles, cupcakes, birthday cakes, and frosting. Capture the Arepa role and revised question. Frame the response as ungrounded, without requiring a particular hallucination. |
| [04-details-endpoint-key.png](../../model-mastery/anthropic/skillable/images/04-details-endpoint-key.png) | 1.1 | **Reuse if deployment details match** | Claude and the Anthropic endpoint remain legitimate configuration details. Recapture if the workshop deployment or portal layout differs; preserve the endpoint-suffix warning. |
| [05-dashboard.png](../../model-mastery/anthropic/skillable/images/05-dashboard.png) | 1.2 | **Replace** | Original has a SPARKLES banner, cupcake art, and a Red Velvet order. Capture Arepa Lab branding and a consented/demo order with a current menu item. Show the distinction between test feed and real pickup. Treat any voucher pictured as illustrative, not reusable. |
| [catering-order.jpg](../../model-mastery/anthropic/sparkles-agent/images/catering-order.jpg) | 1.5, in the runnable agent image folder | **Replace** | Original names Lemon Drop, Red Velvet/Vanilla, Salted Caramel, and Cookies & Cream. Create an Arepa note with exact menu names, tally quantities, one crossed-out replacement, and an allergy note requiring staff escalation. Include a bulk quantity only if the approved FAQ supports the intended catering lesson. |

**Minimum replacement set:** playground, dashboard, and handwritten order.
The deployment image is a recommended fourth refresh. Home and deployment
details can remain when accurate.

For the replacement handwritten note, prepare an expected extraction record:
customer name, exact item names and counts, cancellation/replacement, and
verbatim allergy note. Test the prepared script against this record before
shipping the VM. Strip photo EXIF, particularly GPS metadata.

For all screenshots, redact account details, resource identifiers, secrets,
and real customer data. Use demo data or consented information for the board.
No Lab 2 screenshots need changing within this task's scope.

## Implementation sequence

1. **Resolve the compatibility gates.** Record the actual provisioned names
   and approved policy facts; agree any MCP/persona or packaged-helper changes
   needed to avoid the conflicts above.
2. **Align the runnable materials.** Update the Arepa agent, environment
   example, receipt/catering helpers, completed snapshots, and policy reference
   in the learner package. Keep names and behavior consistent with the MCP.
   The sibling repo is reference material, not the edit target.
3. **Rewrite the eight learner pages together.** Update titles, prose,
   prompts, every repeated code block, console names, configuration references,
   checkpoints, troubleshooting, and timing. Keep Skillable substitutions
   intact. Remove the two-tier requirement and unverified cupcake facts.
4. **Replace and package images.** Supply the root-level screenshots and the
   agent's catering image; update captions and learner-image links. Keep the
   replacement image aligned with the actual menu and script.
5. **Validate from the learner seat.** Use the provisioned VM, configured
   deployment, and both MCP endpoints. Complete a timed rehearsal and adjust
   until the 60-minute maximum is met.

## Acceptance criteria

- All eight pages tell the Arepa Lab story and teach agent behavior, not
  provider capability or model-tier comparison.
- Only one model deployment is required. Technical Claude/Anthropic references
  remain only where needed for accurate setup and API use.
- Skillable credentials and `customerID` capture/reuse still work.
- Every copied code block and snapshot uses the same real configuration,
  paths, tool aliases, policy source, and schema.
- Menu answers use live names/prices/stock labels. No cupcake products,
  fixed 400-cent prices, fabricated IDs, or unverified bakery policies remain
  in learner-facing examples.
- One explicit ordering flow works. Test orders are distinguished from real
  orders; later exercises do not require a second real arepa.
- The two-server exercise uses an approved Arepa policy question and does
  not contradict the server's safety or scope boundaries.
- Structured output is schema-valid and checked against its actual source.
  A request, estimate, or failed order is never presented as a confirmed,
  paid, or collected order.
- The handwritten image matches the menu, and the correction, quantities, and
  allergy-note extraction match the prepared expected record. Allergy
  suitability is escalated, not invented.
- The final evaluation checks observed agent/tool behavior, not only plausible
  prose. Use controlled fixtures or discussion for destructive/error cases;
  do not consume shared stock or trigger lockouts just to demonstrate them.
- Every image and runnable-file reference resolves in the packaged learner
  environment. Completed snapshots support the documented shortcut paths.
- A fresh-VM rehearsal completes guided work in at most 55 minutes and the
  whole session in at most 60 minutes, including the recovery buffer.
