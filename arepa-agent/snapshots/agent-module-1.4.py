"""Arepa Lab ordering agent: completed Module 1.4."""

import asyncio
import json
import os
from contextlib import AsyncExitStack
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import AnthropicFoundryClient

from receipt import OrderCapture, make_receipt
from settings import ROUTING, ToolTrace

# 1. Load the workshop root .env, just as in Module 1.1.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def reply(response) -> str:
    """Arepa Agent's words, with a blank line between what it says before a tool
    call and its answer after (response.text runs them together)."""
    return "\n\n".join(m.text for m in response.messages if m.text)


async def main() -> None:
    # 2. Keep the same configured model client.
    chat_client = AnthropicFoundryClient(
        model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        api_key=os.environ["FOUNDRY_API_KEY"],
        base_url=os.environ["FOUNDRY_ENDPOINT"],
    )
    # Module 1.4: keep confirmed tool data for receipt requests.
    arepa_orders = OrderCapture()
    # The exit stack closes connected servers on normal exit and on exceptions.
    async with AsyncExitStack() as stack:
        # 3. Capture actual order results instead of interpreting the last chat reply.
        arepa_tool = MCPStreamableHTTPTool(
            name="arepa-store",
            url=os.environ["AREPA_MCP_URL"],
            parse_tool_results=arepa_orders.parse_result,
        )
        await arepa_tool.connect()
        stack.push_async_callback(arepa_tool.close)

        # 4. Keep the second MCP connection for documented store policies.
        search_endpoint = os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/")
        search_key = os.environ["AZURE_SEARCH_QUERY_KEY"]
        # Preserve the deployed cupcake resource name; escape it for the URL path.
        kb_name = quote(os.environ.get("KNOWLEDGE_BASE_NAME", "cupcake-store-kb"), safe="")
        arepa_knowledge_tool = MCPStreamableHTTPTool(
            name="arepa-knowledge-base",
            url=f"{search_endpoint}/knowledgebases/{kb_name}/mcp?api-version=2026-08-01-preview",
            header_provider=lambda _: {"api-key": search_key},
            load_prompts=False,
        )
        await arepa_knowledge_tool.connect()
        stack.push_async_callback(arepa_knowledge_tool.close)

        # 5. Combine the server-owned persona with guidance for the two tool sources.
        instructions = await arepa_tool.get_prompt("agent_instructions")
        banner = await arepa_tool.get_prompt("welcome_banner")
        instructions += ROUTING
        # 6. Trace tool names for learning without printing their arguments or results.
        arepa_agent = Agent(
            client=chat_client,
            name="arepa-agent",
            instructions=instructions,
            tools=[arepa_tool, arepa_knowledge_tool],
            middleware=[ToolTrace()],
        )
        # 7. Keep one conversation session and let the store agent greet the customer.
        arepa_session = arepa_agent.create_session()
        print(banner)
        print("Type 'exit' to quit, or 'receipt' after an order.\n")
        response = await arepa_agent.run("hello", session=arepa_session)
        print(f"Arepa Lab:\n{reply(response)}\n")

        # 8. Handle the local receipt command separately from conversational turns.
        while True:
            user_input = input("You:\n").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input:
                continue
            if user_input.lower() == "receipt":
                # Schema-valid JSON must still be backed by a successful tool result.
                if arepa_orders.source is None:
                    print("No confirmed order in this session. Place a test order first.")
                else:
                    print("Order summary, not proof of payment:")
                    print(json.dumps(make_receipt(arepa_orders.source), indent=2))
                continue
            response = await arepa_agent.run(user_input, session=arepa_session)
            print(f"\nArepa Lab:\n{reply(response)}\n")


if __name__ == "__main__":
    asyncio.run(main())
