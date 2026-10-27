# Hands-on Workshop: Building an ordering agent for Arepa Lab

Welcome to Arepa Lab at the SHPE National Convention. Arepas are corn cakes
enjoyed in Venezuela and Colombia. Today you will build the agent that helps
customers discover the menu, place a pickup order, and find store information.

An agent combines a model with instructions, conversation state, and tools.
The model is already deployed for you. This workshop is about how you build
and evaluate the agent around it, not about comparing model providers.

By the end, you will have:

- Seen why a role prompt alone is not a source of store facts.
- Run a Python agent with a conversation session.
- Connected live tools and a server-managed persona through MCP.
- Connected the store's knowledge base through Foundry IQ.
- Produced a schema-checked order summary grounded in a tool result.
- Extracted and reviewed a handwritten request without placing it.
- Evaluated the agent against ordering and safety boundaries.

## Your one-hour route

| Module | Focus | Minutes |
|---|---|---:|
| 1.0 | Instructions and grounding, including this introduction | 5 |
| 1.1 | Agent and session | 7 |
| 1.2 | Store tools, persona, and one order | 12 |
| 1.3 | Store knowledge | 8 |
| 1.4 | Structured order summary | 6 |
| 1.5 | Handwritten request | 8 |
| 1.6 | Agent evaluation and wrap-up | 9 |
| Buffer | Sign-in or recovery | 5 |
| **Total** | | **60** |

Use the prepared code; do not retype entire scripts. The agent has runnable
checkpoints selected with `--module`, so you can catch up without copying
files or losing edits. Each new process starts a fresh conversation.

Module 1.3 builds on 1.2. Module 1.4 uses the same agent or a clearly labeled
simulated result if you need to catch up. Module 1.5 runs separately.
Module 1.6 returns to the grounded agent from 1.3.

## Your environment

Use VS Code, its PowerShell terminal, and the Foundry portal in the provisioned
Skillable VM. Dependencies, the model deployment, the store MCP, and the
knowledge base are ready. The root `.env` is prefilled; do not replace it
with the example file.

The runnable code is in `arepa-agent/`. The same configured model is used
throughout. You will still see its actual client and endpoint names in code.

## Practice versus pickup

The counter accepts one arepa per order and one real arepa per customer.
Test orders do not consume stock or produce food, but still require a valid
dashboard voucher. Use test orders after your first ordering exercise.
This demo does not process payments.

Keep the customer ID the server assigns you and reuse it in later modules.
Never create additional identities to work around an order limit. Food-safety
and dietary-suitability decisions go to staff, not to an inferred answer.
