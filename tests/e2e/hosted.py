"""Read-only validation of the confirmed hosted counter and actual learner client."""

import argparse
import asyncio
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
import logging
import os
from pathlib import Path
import re
import runpy
import sys
from unittest.mock import patch

from dotenv import dotenv_values
import httpx

from support import ROOT, RecordingMCPTool, TOOL_ARGUMENTS

URL = "https://ca-arepa-mcp.yellowbeach-684b8340.eastus.azurecontainerapps.io/mcp/"
READ_ONLY = {"list_arepas", "voucher_status"}
sys.path.insert(0, str(ROOT / "arepa-agent"))
from settings import model_settings


class ReadOnlyTool(RecordingMCPTool):
    def __init__(self, *args, **kwargs):
        kwargs["allowed_tools"] = sorted(READ_ONLY)
        super().__init__(*args, **kwargs)

    async def call_tool(self, tool_name, **kwargs):
        if tool_name not in READ_ONLY:
            raise RuntimeError(f"Hosted validation blocked non-allowlisted tool: {tool_name}")
        return await super().call_tool(tool_name, **kwargs)


def menu_errors(text, menu):
    """Check returned facts in numbered item blocks, allowing natural wording."""
    errors = []
    numbered = re.findall(r"(?m)^\s*\d+[.)]\s+(.+?(?=^\s*\d+[.)]\s+|\Z))", text, re.S)
    if not menu:
        if numbered or not re.search(r"no .*(?:arepas|items|menu)|unavailable|empty", text, re.I):
            errors.append("Empty menu was not acknowledged without invented choices.")
        return errors
    for item in menu:
        blocks = [block for block in numbered if item["name"].casefold() in block.casefold()]
        if len(blocks) != 1:
            errors.append(f"{item['name']}: expected exactly one numbered item.")
            continue
        block = blocks[0]
        description = item.get("description", "").strip()
        if description:
            if description.casefold().rstrip(".") not in block.casefold():
                errors.append(f"{item['name']}: returned description missing.")
        elif not re.search(r"description.{0,30}(?:unavailable|not (?:provided|available))|"
                           r"no description", block, re.I):
            errors.append(f"{item['name']}: missing description not acknowledged.")
        price = f"{item['price']:.2f}"
        if not re.search(rf"(?:USD\s*|\$\s*){re.escape(price)}(?!\d)|"
                         rf"(?<!\d){re.escape(price)}\s*USD\b", block, re.I):
            errors.append(f"{item['name']}: USD price missing or incorrect.")
        if item["stock_label"].casefold() not in block.casefold():
            errors.append(f"{item['name']}: stock_label missing.")
        slug = item["id"]
        if slug.casefold() != item["name"].casefold() and slug.casefold() in text.casefold():
            errors.append(f"{item['name']}: internal machine ID exposed.")
    if len(numbered) != len(menu):
        errors.append("Numbered menu count differs from the returned menu.")
    return errors


async def validate(args):
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "requested_url": URL.rstrip("/"), "canonical_url": URL,
        "model_requested": args.model, "model_deployment": None, "checks": [],
    }

    def check(name, passed, detail):
        report["checks"].append({"name": name, "status": "pass" if passed else "fail", "detail": detail})

    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as http:
        response = await http.get(URL.rstrip("/"))
        location = response.headers.get("location")
        check("canonical_path", response.status_code in (307, 308) and location == URL,
              {"status": response.status_code, "location": location})
    tool = ReadOnlyTool(name="hosted-read-only", url=URL)
    await tool.connect()
    try:
        discovered = (await tool.session.list_tools()).tools
        check("seven_tool_contract", len(discovered) == 7 and all(
            t.name in TOOL_ARGUMENTS
            and set(t.inputSchema.get("required", [])) == TOOL_ARGUMENTS[t.name]
            and set(t.inputSchema["properties"]) == TOOL_ARGUMENTS[t.name]
            for t in discovered
        ), {"tools": sorted(t.name for t in discovered)})
        prompts = (await tool.session.list_prompts()).prompts
        instructions = await tool.get_prompt("agent_instructions")
        banner = await tool.get_prompt("welcome_banner")
        check("both_server_prompts",
              {p.name for p in prompts} == {"agent_instructions", "welcome_banner"}
              and bool(instructions.strip()) and "AREPA LAB" in banner,
              {"prompts": sorted(p.name for p in prompts)})
        missing = [field for field in ("description", "price", "stock_label")
                   if field not in instructions.lower()]
        check("server_menu_instructions", not missing,
              {"missing_required_guidance": missing})
        menu = await tool.call("list_arepas")
        valid = isinstance(menu, list) and all(
            isinstance(item, dict)
            and {"id", "name", "description", "price", "stock_label"} <= item.keys()
            and all(isinstance(item[k], str) for k in ("id", "name", "description", "stock_label"))
            and isinstance(item["price"], (int, float)) and not isinstance(item["price"], bool)
            and item["price"] >= 0
            for item in menu
        )
        check("live_menu_contract", valid, {"item_count": len(menu) if isinstance(menu, list) else None})
        timing = await tool.call("voucher_status")
        check("voucher_timing", set(timing) == {"seconds_until_rotation", "window_seconds", "message"}
              and 0 < timing["seconds_until_rotation"] <= timing["window_seconds"],
              {k: timing[k] for k in ("seconds_until_rotation", "window_seconds")})
    finally:
        await tool.close()
    check("adapter_cleanup", not tool.is_connected, "Read-only MCP adapter closed.")

    if args.model:
        values = dotenv_values(args.env_file)
        model_env = {key: os.environ.get(key) or values.get(key) or ""
                     for key in ("FOUNDRY_ENDPOINT", "FOUNDRY_API_KEY", "FOUNDRY_MODEL_DEPLOYMENT")}
        missing = [k for k, v in model_env.items() if not v.strip() or "<" in v or ">" in v]
        invalid_endpoint = False
        if not missing:
            try:
                with patch.dict(os.environ, model_env):
                    config = model_settings()
            except ValueError:
                invalid_endpoint = True
        if missing or invalid_endpoint:
            report["checks"].append({"name": "model_menu_conversation", "status": "blocked",
                                     "detail": {
                                         "missing_settings": missing,
                                         "unsupported_endpoint": invalid_endpoint,
                                     }})
        else:
            report["model_deployment"] = model_env["FOUNDRY_MODEL_DEPLOYMENT"]
            report["model_protocol"] = (
                "OpenAI-compatible" if config["base_url"].endswith("/openai/v1") else "Anthropic"
            )
            instances = []
            class ObservedTool(ReadOnlyTool):
                def __init__(self, *a, **kw):
                    super().__init__(*a, **kw)
                    instances.append(self)

            namespace = runpy.run_path(str(ROOT / "arepa-agent/snapshots/agent-module-1.2.py"))
            main = namespace["main"]
            main.__globals__["MCPStreamableHTTPTool"] = ObservedTool
            output = io.StringIO()
            try:
                with patch.dict(os.environ, {**model_env, "AREPA_MCP_URL": URL}), \
                     patch("builtins.input", side_effect=[
                         "Show today's live menu only; do not register me or place an order.", "exit",
                     ]), redirect_stdout(output):
                    await asyncio.wait_for(main(), timeout=180)
                calls = [c for instance in instances for c in instance.calls]
                menu_calls = [c for c in calls if c["tool"] == "list_arepas"]
                transcript = output.getvalue()
                # Only evaluate the final conversational reply, not the banner/greeting.
                answer = transcript.rsplit("Arepa Lab:\n", 1)[-1].strip()
                errors = menu_errors(answer, menu_calls[-1]["result"]) if menu_calls else ["No list_arepas call."]
                check("model_menu_conversation", not errors, {
                    "tool_calls": [c["tool"] for c in calls],
                    "menu_item_count": len(menu_calls[-1]["result"]) if menu_calls else None,
                    "errors": errors, "answer": answer,
                })
            except Exception as exc:
                # Do not log exception text: SDK errors may include request details.
                check("model_menu_conversation", False, {
                    "error_type": type(exc).__name__, "status_code": getattr(exc, "status_code", None),
                })
            finally:
                for instance in instances:
                    if instance.is_connected:
                        await instance.close()
            check("learner_client_cleanup", bool(instances) and all(
                not t.is_connected for t in instances
            ), "Observed learner client connections closed.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", action="store_true")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        report = asyncio.run(validate(args))
    except Exception as exc:
        report = {
            "canonical_url": URL, "model_deployment": None,
            "checks": [{"name": "hosted_transport", "status": "fail",
                        "detail": {"error_type": type(exc).__name__,
                                   "status_code": getattr(exc, "status_code", None)}}],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    counts = {status: sum(c["status"] == status for c in report["checks"])
              for status in ("pass", "fail", "blocked")}
    print(json.dumps({"canonical_url": URL, "model_deployment": report["model_deployment"],
                      **counts}, indent=2))
    return 0 if not counts["fail"] and not counts["blocked"] else 1


if __name__ == "__main__":
    sys.exit(main())
