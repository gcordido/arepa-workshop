"""Arepa Lab ordering agent: completed Module 1.3."""

import asyncio
import os
from contextlib import AsyncExitStack
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

from agent_framework import Agent, MCPStreamableHTTPTool
from settings import ROUTING, ToolTrace, create_chat_client

# 1. Load the workshop root .env, just as in Module 1.1.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def reply(response) -> str:
    """Arepa Agent's words, with a blank line between what it says before a tool
    call and its answer after (response.text runs them together)."""
    return "\n\n".join(m.text for m in response.messages if m.text)


async def main() -> None:
    # 2. Keep the same configured model client.
    chat_client = create_chat_client()

    # 3. Discover the store tools; close connected servers on exit or error.
    async with AsyncExitStack() as stack:
        arepa_tool = MCPStreamableHTTPTool(
            name="arepa-store",
            url=os.environ["AREPA_MCP_URL"],
        )
        await arepa_tool.connect()
        stack.push_async_callback(arepa_tool.close)

        # 4. Add policy retrieval using a read-only Search query key.
        search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
        search_key = os.environ["AZURE_SEARCH_QUERY_KEY"]
        # Keep the existing Azure resource name, escaped as a URL path segment.
        kb_name = quote(os.environ.get("KNOWLEDGE_BASE_NAME", "cupcake-store-kb"), safe="")
        arepa_knowledge_tool = MCPStreamableHTTPTool(
            name="arepa-knowledge-base",
            url=f"{search_endpoint}/knowledgebases/{kb_name}/mcp?api-version=2026-08-01-preview",
            header_provider=lambda _: {"api-key": search_key},
            load_prompts=False,
        )
        await arepa_knowledge_tool.connect()
        stack.push_async_callback(arepa_knowledge_tool.close)

        # 5. Combine the store persona with guidance for the two tool sources.
        instructions = await arepa_tool.get_prompt("agent_instructions")
        banner = await arepa_tool.get_prompt("welcome_banner")
        instructions += ROUTING

        # 6. Both servers are available; the agent selects tools per question.
        arepa_agent = Agent(
            client=chat_client,
            name="arepa-agent",
            instructions=instructions,
            tools=[arepa_tool, arepa_knowledge_tool],
            middleware=[ToolTrace()],
        )

        # 7. Keep one session and let the agent greet the customer first.
        arepa_session = arepa_agent.create_session()
        print(banner)
        print("Type 'exit' to quit.\n")
        response = await arepa_agent.run("hello", session=arepa_session)
        print(f"Arepa Lab:\n{reply(response)}\n")

        # 8. Both tool servers remain available throughout the conversation.
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
