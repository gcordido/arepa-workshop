"""Shared configuration for the provisioned learner environment."""

import os
from collections.abc import Awaitable, Callable
from pathlib import Path

from agent_framework import FunctionInvocationContext, FunctionMiddleware
from dotenv import load_dotenv

# 1. Find the workshop .env independently of the terminal's current directory.
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# 2. Separate retail-policy knowledge from actions supported by the live counter.
ROUTING = (
    "\n\nUse arepa-store for live menu, customer lookup, orders and status. "
    "Use arepa-knowledge-base for store hours, delivery, returns, allergens, "
    "loyalty and bulk-order policies. Retail policies describe the store scenario; "
    "they do not authorize bulk checkout, payments or extra real orders through "
    "the workshop counter. Never infer allergen safety or dietary suitability; "
    "refer those decisions to staff. Do not invent store information; look it up."
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
    # The client adds /v1/messages itself; do not include it twice in the endpoint.
    endpoint = setting("FOUNDRY_ENDPOINT").rstrip("/")
    if not endpoint.endswith("/anthropic"):
        raise ValueError("FOUNDRY_ENDPOINT must end at /anthropic, not /v1/messages.")
    return {
        "model": setting("FOUNDRY_MODEL_DEPLOYMENT"),
        "api_key": setting("FOUNDRY_API_KEY"),
        "base_url": endpoint,
    }
