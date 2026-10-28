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