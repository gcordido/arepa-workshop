"""Arepa Lab ordering agent (Module 1.1 starting point)

You will grow this file through Lab 1. Each module adds a small, marked
block. Completed versions of every module live in snapshots/ if you need
to catch up.
"""
import asyncio
from pathlib import Path

from dotenv import load_dotenv

from agent_framework import Agent
from settings import create_chat_client

# 1. Load settings from .env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def reply(response) -> str:
    """Arepa Agent's words, with a blank line between what it says before a tool
    call and its answer after (response.text runs them together)."""
    return "\n\n".join(m.text for m in response.messages if m.text)

async def main() -> None:
    # 2. The configured model client; store tools are added in Module 1.2.
    chat_client = create_chat_client()

    # 3. The agent starts without store instructions or tools.
    arepa_agent = Agent(client=chat_client, name="arepa-agent")

    # 4. A session keeps the conversation history
    arepa_session = arepa_agent.create_session()
    print("Arepa Lab agent ready. Type 'exit' to quit.\n")

    # 5. Reuse this session for every turn so the agent remembers the conversation.
    while True:
        user_input = input("You:\n").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue
        response = await arepa_agent.run(user_input, session=arepa_session)
        print(f"\nArepa Lab:\n{reply(response)}\n")


if __name__ == "__main__":
    asyncio.run(main())
