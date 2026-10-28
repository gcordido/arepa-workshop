"""Module 1.5: vision, an agent with both tool servers, and a request receipt."""

import argparse
import asyncio
import base64
import json
from collections.abc import Awaitable, Callable, Mapping
from contextlib import AsyncExitStack
from pathlib import Path
from urllib.parse import quote

from anthropic import AnthropicFoundry
from agent_framework import Agent, FunctionInvocationContext, MCPStreamableHTTPTool, MiddlewareFailure
from agent_framework.foundry import AnthropicFoundryClient

from receipt import OrderCapture, checked_json, make_receipt, make_request_receipt
from settings import ROUTING, ToolTrace, model_settings, reply, setting

# 1. Extract the customer's request, including corrections and unresolved details.
ORDER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "customer": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    # An unreadable quantity stays unknown instead of becoming a guess.
                    "quantity": {"type": ["integer", "null"], "minimum": 1},
                },
                "required": ["name", "quantity"],
            },
        },
        "allergy_notes": {"type": "string"},
        "corrections_applied": {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "customer", "items", "allergy_notes", "corrections_applied", "uncertainties"
    ],
}


def read_order(path: Path) -> dict[str, object]:
    # 2. Encode the photo as an image block and request schema-constrained extraction.
    media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    media_type = media_types.get(path.suffix.lower())
    if media_type is None:
        raise ValueError("Use a JPEG or PNG photo of the Arepa request.")
    data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    settings = model_settings()
    with AnthropicFoundry(
        api_key=settings["api_key"], base_url=settings["base_url"]
    ) as client:
        response = client.messages.create(
            model=settings["model"],
            max_tokens=1200,
            output_config={"format": {"type": "json_schema", "schema": ORDER_SCHEMA}},
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": media_type, "data": data
                    }},
                    {"type": "text", "text": (
                        "Extract this Arepa Lab handwritten REQUEST, not an accepted order. "
                        "Crossed-out items are cancelled; use the written replacement. "
                        "Count tally marks; use null for an unreadable quantity "
                        "and record the uncertainty instead of guessing. "
                        "Copy the allergy note verbatim. "
                        "List corrections and anything illegible in uncertainties. "
                        "Do not infer ingredients, safety, prices or missing items. "
                        "Use an empty customer string if no name is readable."
                    )},
                ],
            }],
        )
    # Select text explicitly because other response block types may come first.
    text = next((b.text for b in response.content if b.type == "text"), None)
    if text is None:
        raise ValueError("Model returned no text; the photo was not extracted.")
    return checked_json(text, ORDER_SCHEMA)


class TestOrdersOnly(ToolTrace):
    async def process(
        self, context: FunctionInvocationContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        # 3. Enforce test-only practice in code, not just in the agent's instructions.
        if context.function.name == "order_arepa":
            arguments = context.arguments
            kind = arguments.get("kind") if isinstance(arguments, Mapping) else getattr(arguments, "kind", None)
            if kind != "test":
                raise MiddlewareFailure("Catering practice permits test orders only; no real order was sent.")
        await super().process(context, call_next)


async def work_order(arepa_request: dict[str, object]) -> dict[str, object] | None:
    # 4. Give the validated request to an agent with live store tools and policy search.
    checked_json(json.dumps(arepa_request), ORDER_SCHEMA)
    chat_client = AnthropicFoundryClient(**model_settings())
    arepa_orders = OrderCapture()
    # Close both connected servers even if retrieval or a later model call fails.
    async with AsyncExitStack() as stack:
        arepa_tool = MCPStreamableHTTPTool(
            name="arepa-store", url=setting("AREPA_MCP_URL"),
            parse_tool_results=arepa_orders.parse_result,
            # Reuse the learner's ID: registration and cancellation are not exposed.
            allowed_tools=[
                "get_customer", "list_arepas", "order_arepa",
                "check_order_status", "voucher_status",
            ],
        )
        await arepa_tool.connect()
        stack.push_async_callback(arepa_tool.close)
        # 5. Connect IQ using the query key and the unchanged Azure KB identifier.
        search_endpoint = setting("AZURE_SEARCH_ENDPOINT").rstrip("/")
        search_key = setting("AZURE_SEARCH_QUERY_KEY")
        kb_name = quote(setting("KNOWLEDGE_BASE_NAME"), safe="")
        arepa_knowledge_tool = MCPStreamableHTTPTool(
            name="arepa-knowledge-base",
            url=f"{search_endpoint}/knowledgebases/{kb_name}/mcp?api-version=2026-08-01-preview",
            header_provider=lambda _: {"api-key": search_key},
            load_prompts=False,
        )
        await arepa_knowledge_tool.connect()
        stack.push_async_callback(arepa_knowledge_tool.close)
        # 6. Keep the store persona, then add policy routing and practice boundaries.
        instructions = await arepa_tool.get_prompt("agent_instructions")
        instructions += ROUTING + (
            "\nThis is catering practice. Do not register customers or cancel orders. "
            "Reuse the learner's existing customer ID. Never place a real order. "
            "First review the request; do not order until the learner explicitly "
            "authorizes ONE test order and selects an item. Resolve uncertainties "
            "with the learner and refer allergy suitability to staff, not inference. "
            "A test order does not establish safety or confirm the catering request."
        )
        arepa_agent = Agent(
            client=chat_client, name="arepa-agent", instructions=instructions,
            tools=[arepa_tool, arepa_knowledge_tool], middleware=[TestOrdersOnly()],
        )
        # 7. Review policy and availability before asking the learner about any test.
        arepa_session = arepa_agent.create_session()
        brief = (
            "Review this handwritten Arepa catering REQUEST, not an accepted order:\n"
            + json.dumps(arepa_request)
            + "\nLook up the store's allergen and bulk-order policies, including "
            "the quantity threshold, notice and deposit. Check the live menu and "
            "explain availability and any uncertainties. Refer safety decisions to "
            "staff. Explain what staff must handle outside the single-item counter. "
            "Do not place an order yet."
        )
        response = await arepa_agent.run(brief, session=arepa_session)
        print(f"\nArepa Lab:\n{reply(response)}\n")
        # Follow-up turns reuse the session; "done" ends practice without ordering.
        while True:
            user_input = input("You (type 'done' when finished):\n").strip()
            if user_input.lower() in ("done", "exit", "quit"):
                break
            if user_input:
                response = await arepa_agent.run(user_input, session=arepa_session)
                print(f"\nArepa Lab:\n{reply(response)}\n")
        return arepa_orders.source


async def main(image: Path | None, extracted: Path | None) -> None:
    # 8. The prepared JSON is a catch-up path, not evidence that vision succeeded.
    if extracted:
        order = checked_json(extracted.read_text(encoding="utf-8"), ORDER_SCHEMA)
        print("PRE-EXTRACTED FALLBACK: vision was not run.")
    elif image:
        order = read_order(image)
        print("Compare this extraction with the photo before using it:")
    else:
        raise ValueError("An image or extracted request is required.")
    print(json.dumps(order, indent=2))
    # Human review comes before the extracted request is handed to an acting agent.
    confirmed = input("Does this extraction match the note? Type 'yes' to continue:\n").strip()
    if confirmed.lower() != "yes":
        raise ValueError("Extraction not confirmed. Correct the request with your instructor before continuing.")
    arepa_order = await work_order(order)
    # 9. Keep an accepted single-item test separate from the entire catering request.
    if arepa_order is not None:
        print("Confirmed counter test order (not a catering confirmation or payment):")
        print(json.dumps(make_receipt(arepa_order), indent=2))
    print("Receipt for the whole REQUEST: nothing here confirms catering or payment.")
    print(json.dumps(make_request_receipt(order), indent=2))


if __name__ == "__main__":
    # Use the prepared photo by default, or explicitly choose the JSON fallback.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", type=Path)
    parser.add_argument("--extracted", type=Path, help="Review JSON without running vision.")
    args = parser.parse_args()
    if args.image is not None and args.extracted is not None:
        parser.error("Provide either an image or --extracted, not both.")
    if args.image is None and args.extracted is None:
        args.image = Path(__file__).resolve().parent / "images" / "catering-order.jpg"
    asyncio.run(main(args.image, args.extracted))
