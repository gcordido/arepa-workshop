## Module 1.1: An agent and a session (7 minutes)

Open VS Code from the Desktop shortcut. The workshop project and Python
environment are already prepared.

### Check the configuration

Open `.env` at the project root. Leave its supplied values unchanged.
These settings identify the model client:

```dotenv
FOUNDRY_ENDPOINT="https://<your-resource>.services.ai.azure.com/anthropic"
FOUNDRY_API_KEY="<provided-key>"
FOUNDRY_MODEL_DEPLOYMENT="<provided-deployment-name>"
```

The chosen model uses `AnthropicFoundryClient`. This is a technical client
choice, not a second set of lab objectives. Keep the same deployment
throughout the workshop.

The endpoint must end at `/anthropic`, not `/anthropic/v1/messages`.
The client adds `/v1/messages` itself. Appending it twice causes a 404.

> Treat the key like a password. Do not paste it into chat or screenshots.
> The repository ignores `.env`; `.env.example` contains placeholders only.

### Read the starting checkpoint

Open `arepa-agent/agent.py`. Focus on these lines:

```python
client = AnthropicFoundryClient(**model_settings())
agent = Agent(client=client, name="arepa-agent", instructions=instructions, tools=tools)
session = agent.create_session()
```

At checkpoint 1.1, the instruction string and tool list are empty.

1. The **client** handles the configured model connection.
2. The **agent** combines that client with instructions and tools.
3. The **session** keeps conversation history between `agent.run` calls.

The terminal loop reads your text, runs the agent with that session, and
prints its reply. Starting a new process creates a new session.

### Run it

Select **Terminal > New Terminal**. From the project root, run:

```powershell
cd arepa-agent
python agent.py --module 1.1
```

Say `Hello!`, then `My name is Alex.`, then `What name did I give you?`.
The last reply should use the conversation history. Type `exit`.

**Checkpoint 2.** Your Python agent runs, and its session keeps context
between turns. It still has no live store tools.

If a setting is missing, check the root `.env` with your instructor. A 401
usually means authentication or endpoint configuration needs checking;
`DeploymentNotFound` means the deployment name does not match. Do not spend
the lab installing packages or creating deployments.

<!-- Reuse the audited deployment-details image only if its navigation,
deployment, and endpoint still match the supplied VM. -->
