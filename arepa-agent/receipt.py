"""Module 1.4: a schema-checked summary of a supplied order-tool result.

The default input is an explicitly simulated test result, not a live order.
"""

import argparse
import json
from pathlib import Path

from jsonschema import validate
from mcp.types import CallToolResult

from settings import structured_output

# 1. Describe a single confirmed counter order, not a payment or catering receipt.
RECEIPT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "item": {"type": "string"},
        "quantity": {"type": "integer", "enum": [1]},
        "kind": {"type": "string", "enum": ["test", "real"]},
        "status": {"type": "string", "enum": ["confirmed"]},
        "payment_processed": {"type": "boolean", "enum": [False]},
    },
    "required": ["item", "quantity", "kind", "status", "payment_processed"],
}

# Standalone practice uses this simulated result; it creates no live order.
SAMPLE_RESULT = {
    "success": True,
    "kind": "test",
    "flavor": "Catira",
}


class OrderCapture:
    """Keep only the latest confirmed order's public summary fields."""

    def __init__(self) -> None:
        self.source: dict[str, object] | None = None

    def parse_result(self, result: CallToolResult) -> str:
        # 2. Read structured MCP data when supplied, otherwise parse its JSON text.
        if result.isError:
            self.source = None
        texts = [block.text for block in result.content if block.type == "text"]
        try:
            if result.structuredContent is not None:
                data = result.structuredContent
            elif texts:
                data = json.loads(texts[0])
            else:
                raise ValueError("Store tool returned no JSON result.")
        except ValueError:
            self.source = None
            raise
        if isinstance(data, dict):
            if data.get("success") is False:
                self.source = None
            elif data.get("success") is True:
                # A successful registration/cancellation must not leave an old receipt.
                self.source = None
                # Cancellation also returns kind and flavor; only an accepted
                # order includes the public board_name in the seven-tool contract.
                if all(key in data for key in ("kind", "flavor", "board_name")) and not result.isError:
                    expected_summary(data)
                    # Keep only public fields; do not persist internal order identifiers.
                    self.source = {
                        "success": True, "kind": data["kind"], "flavor": data["flavor"]
                    }
        return json.dumps(data)


def expected_summary(source: dict[str, object]) -> dict[str, object]:
    # 3. Validate the source before labeling anything confirmed.
    if source.get("success") is not True:
        raise ValueError("Cannot summarize an unconfirmed or failed order as confirmed.")
    if source.get("kind") not in ("test", "real"):
        raise ValueError("Order result must specify kind as test or real.")
    flavor = source.get("flavor")
    if not isinstance(flavor, str) or not flavor.strip():
        raise ValueError("Order result must contain its returned flavor name.")
    return {
        "item": flavor,
        "quantity": 1,
        "kind": source["kind"],
        "status": "confirmed",
        "payment_processed": False,
    }


def checked_json(text: str, schema: dict) -> dict[str, object]:
    # API-constrained output is also validated locally before the program uses it.
    value = json.loads(text)
    validate(instance=value, schema=schema)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")
    return value


def make_request_receipt(arepa_request: dict[str, object]) -> dict[str, object]:
    """Keep the entire catering request separate from any accepted counter order."""
    # 4. The whole catering request remains "requested", even after one counter test.
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {"const": "requested"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "quantity": {"type": ["integer", "null"], "minimum": 1},
                    },
                    "required": ["name", "quantity"],
                },
            },
            "allergy_notes": {"type": "string"},
            "payment_processed": {"const": False},
        },
        "required": ["status", "items", "allergy_notes", "payment_processed"],
    }
    summary = {
        "status": "requested", "items": arepa_request["items"],
        "allergy_notes": arepa_request["allergy_notes"], "payment_processed": False,
    }
    validate(instance=summary, schema=schema)
    return summary


def make_receipt(source: dict[str, object]) -> dict[str, object]:
    # 5. Establish the expected facts first, then ask for schema-constrained output.
    expected = expected_summary(source)
    text = structured_output(
        "Return this order summary exactly, without changing any values. "
        "It is not a payment receipt. Do not add identifiers or prices.\n"
        + json.dumps(expected),
        RECEIPT_SCHEMA, max_tokens=500,
    )
    summary = checked_json(text, RECEIPT_SCHEMA)
    # 6. Correct JSON shape does not guarantee correct item names or order facts.
    if summary != expected:
        raise ValueError("Schema-valid output disagrees with the source order result.")
    return summary


if __name__ == "__main__":
    # Run independently with a simulated result, or a supplied successful tool result.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path,
        help="Instructor-provided JSON containing an actual order_arepa success result.",
    )
    args = parser.parse_args()
    if args.source:
        source = json.loads(args.source.read_text(encoding="utf-8"))
        if not isinstance(source, dict):
            parser.error("--source must contain a JSON object from order_arepa")
        print("Summary of supplied order result (not proof of payment):")
    else:
        source = SAMPLE_RESULT
        print("SIMULATED TEST RESULT: no live order or payment is created.")
    print(json.dumps(make_receipt(source), indent=2))
