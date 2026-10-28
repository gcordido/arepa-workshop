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

Open `arepa-agent/agent.py`. The imports are:

<!-- build: imports -->
```python
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from agent_framework import Agent
from agent_framework.foundry import AnthropicFoundryClient
```

The provided file loads the **root** `.env` using its file path and defines
`reply(response)` to separate text before and after tool calls. Keep both
of these unchanged throughout Modules 1.1-1.4, along with the final
`if __name__ == "__main__":` entry point.

Here is the starting `main()` function. You will replace this function in
each following module, not add a second `main()`:

<!-- build: main -->
```python
async def main() -> None:
    # 2. The configured model client; store tools are added in Module 1.2.
    chat_client = AnthropicFoundryClient(
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        api_key=os.environ["FOUNDRY_API_KEY"],
        base_url=os.environ["FOUNDRY_ENDPOINT"],
    )

    # 3. The agent starts without store instructions or tools.
    arepa_agent = Agent(client=chat_client, name="arepa-agent")

    # 4. A session keeps the conversation history.
    arepa_session = arepa_agent.create_session()
    print("Arepa Lab agent ready. Type 'exit' to quit.\n")

    # 5. Reuse this session for every conversational turn.
    while True:
        user_input = input("You:\n").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue
        response = await arepa_agent.run(user_input, session=arepa_session)
        print(f"\nArepa Lab:\n{reply(response)}\n")
```

1. The **client** handles the configured model connection.
2. The **agent** combines that client with instructions and tools.
3. The **session** keeps conversation history between `agent.run` calls.

The terminal loop reads your text, runs the agent with that session, and
prints its reply. Starting a new process creates a new session.

### Run it

Select **Terminal > New Terminal**. From the project root, run:

```powershell
cd arepa-agent
python agent.py
```

Say `Hello!`, then `My name is Eugenia.`, then `What name did I give you?`.
The last reply should use the conversation history. Type `exit`.

**Checkpoint 2.** Your Python agent runs, and its session keeps context
between turns. It still has no live store tools.

If a setting is missing, check the root `.env` with your instructor. A 401
usually means authentication or endpoint configuration needs checking;
`DeploymentNotFound` means the deployment name does not match. Do not spend
the lab installing packages or creating deployments.

<!-- Reuse the audited deployment-details image only if its navigation,
deployment, and endpoint still match the supplied VM. -->
