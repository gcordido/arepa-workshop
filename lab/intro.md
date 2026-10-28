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
- Read a handwritten request, applied store policy, and optionally placed one
  counter test order without accepting the full catering request.
- Evaluated the agent against ordering and safety boundaries.


**How the lab works.** Every module ends with a checkpoint. Modules 1.4 through
1.6 are independent, so if you fall behind, skip to the next one. Completed
code for Modules 1.1-1.4 is in
[arepa-agent/snapshots/](../arepa-agent/snapshots/); copy the one you
need over `agent.py` and carry on. Module 1.5 uses the prepared `catering.py`
helper; Module 1.6 returns to the Module 1.3 snapshot.

**Your environment.** You will use VS Code with the repo open, its terminal, and the Foundry portal in a browser tab. The modules tell you when to open each one. The '.env' file at the top of the repo is already filled in for you unless the instructor says otherwise.
