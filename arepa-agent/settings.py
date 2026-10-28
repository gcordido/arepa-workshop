"""Shared configuration for the provisioned learner environment."""

import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from agent_framework import FunctionInvocationContext, FunctionMiddleware, SupportsChatGetResponse
from dotenv import load_dotenv

# 1. Find the workshop .env independently of the terminal's current directory.
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# 2. Separate retail-policy knowledge from actions supported by the live counter.
ROUTING = (
    "\n\nUse arepa-store for the live menu, eligibility, customer lookup, "
    "order limits, orders, status and pending-only cancellation. "
    "Use arepa-knowledge-base for fictional retail store hours, delivery, "
    "payment, refunds, cancellation, loyalty and bulk-order policies. "
    "Those fictional policies cannot override the live workshop counter or "
    "authorize bulk checkout, payments, deposits or extra real orders. "
    "Never apply retail cancellation windows to counter orders. "
    "Neither source establishes allergen safety or dietary suitability; "
    "refer actual ingredients, preparation and suitability to staff. "
    "Do not invent store information; look it up."
)


class ToolTrace(FunctionMiddleware):
    async def process(
        self,
        context: FunctionInvocationContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        # Observe tool selection without exposing customer data, vouchers or keys.
        print(f"[tool] {context.function.name}")
        await call_next()


def reply(response) -> str:
    # Separate text before and after tool calls instead of running it together.
    return "\n\n".join(message.text for message in response.messages if message.text)


def setting(name: str) -> str:
    # Fail visibly on missing configuration rather than using example placeholders.
    value = os.environ.get(name, "").strip()
    if not value or "<" in value or ">" in value:
        raise ValueError(f"Set {name} in the workshop root .env; ask your instructor.")
    return value


def model_settings() -> dict[str, str]:
    endpoint = urlsplit(setting("FOUNDRY_ENDPOINT").rstrip("/"))
    project = endpoint.path.partition("/api/projects/")[2]
    if project and "/" not in project:
        endpoint = endpoint._replace(path=endpoint.path + "/openai/v1")
    if not endpoint.path.endswith(("/anthropic", "/openai/v1")):
        raise ValueError(
            "FOUNDRY_ENDPOINT must end at /anthropic or /openai/v1, "
            "or identify a Foundry /api/projects/<project> endpoint; "
            "do not append /v1/messages or /chat/completions."
        )
    return {
        "model": setting("FOUNDRY_MODEL_DEPLOYMENT"),
        "api_key": setting("FOUNDRY_API_KEY"),
        "base_url": endpoint.geturl(),
    }


def create_chat_client() -> SupportsChatGetResponse:
    config = model_settings()
    if urlsplit(config["base_url"]).path.endswith("/openai/v1"):
        from agent_framework.openai import OpenAIChatClient

        return OpenAIChatClient(**config)
    from agent_framework.foundry import AnthropicFoundryClient

    return AnthropicFoundryClient(**config)


def structured_output(
    prompt: str, schema: dict, *, max_tokens: int,
    image: tuple[Literal["image/jpeg", "image/png"], str] | None = None,
) -> str:
    """Request constrained JSON; callers still validate its shape and source facts."""
    config = model_settings()
    if urlsplit(config["base_url"]).path.endswith("/openai/v1"):
        from openai import OpenAI
        from openai.types.chat import ChatCompletionContentPartParam

        parts: list[ChatCompletionContentPartParam] = []
        if image is not None:
            media_type, data = image
            parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{data}"},
            })
        parts.append({"type": "text", "text": prompt})
        with OpenAI(api_key=config["api_key"], base_url=config["base_url"]) as openai_client:
            openai_response = openai_client.chat.completions.create(
                model=config["model"],
                # Reasoning models share this budget with the visible JSON output.
                max_completion_tokens=max_tokens + 2048,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "workshop_output", "strict": True, "schema": schema},
                },
                messages=[{"role": "user", "content": parts}],
            )
        if not openai_response.choices:
            raise ValueError("Model returned no choices; no structured output was produced.")
        choice = openai_response.choices[0]
        if choice.message.refusal:
            raise ValueError("Model refused the request; no structured output was produced.")
        if choice.finish_reason == "length":
            raise ValueError("Model output was truncated; no structured output was accepted.")
        text = choice.message.content
    else:
        from anthropic import AnthropicFoundry
        from anthropic.types import ContentBlockParam

        blocks: list[ContentBlockParam] = []
        if image is not None:
            media_type, data = image
            blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": data},
            })
        blocks.append({"type": "text", "text": prompt})
        with AnthropicFoundry(api_key=config["api_key"], base_url=config["base_url"]) as anthropic_client:
            anthropic_response = anthropic_client.messages.create(
                model=config["model"], max_tokens=max_tokens,
                output_config={"format": {"type": "json_schema", "schema": schema}},
                messages=[{"role": "user", "content": blocks}],
            )
        if anthropic_response.stop_reason in ("max_tokens", "refusal"):
            raise ValueError("Model stopped before accepting structured output.")
        text = next((block.text for block in anthropic_response.content if block.type == "text"), None)
    if not text:
        raise ValueError("Model returned no text; no structured output was produced.")
    return text
