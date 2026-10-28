"""Offline tests of hosted validation; these tests never open a connection."""

import asyncio
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

from agent_framework import Content

sys.path.insert(0, str(Path(__file__).parent / "e2e"))
from hosted import ReadOnlyTool, menu_errors
from support import RecordingMCPTool, decode_result


class HostedSafetyTests(unittest.TestCase):
    menu = [
        {"id": "test-item-one", "name": "Synthetic One", "description": "First filling",
         "price": 6.25, "stock_label": "Plenty"},
        {"id": "test-item-two", "name": "Synthetic Two", "description": "",
         "price": 4.00, "stock_label": "Almost finished"},
    ]
    answer = (
        "1. Synthetic One: First filling. $6.25 USD. Plenty.\n"
        "2. Synthetic Two: description unavailable. $4.00 USD. Almost finished."
    )

    def test_complete_numbered_menu_and_missing_description(self):
        self.assertEqual(menu_errors(self.answer, self.menu), [])

    def test_each_field_is_required_on_every_item(self):
        for before, after in (
            ("First filling", ""), ("$6.25 USD", ""), ("Almost finished", ""),
            ("description unavailable", ""), ("2. Synthetic Two", "Synthetic Two"),
            ("Synthetic One", "Invented Item"),
        ):
            with self.subTest(field=before):
                self.assertTrue(menu_errors(self.answer.replace(before, after), self.menu))
        self.assertTrue(menu_errors(self.answer + "\ntest-item-one", self.menu))
        self.assertTrue(menu_errors(self.answer + "\n3. Invented Item: $1.00", self.menu))

    def test_empty_menu_cannot_invent_choices(self):
        self.assertEqual(menu_errors("No arepas are available. Please ask staff.", []), [])
        self.assertTrue(menu_errors("1. Invented Arepa $3.00", []))

    def test_adapter_blocks_every_write_before_transport(self):
        tool = ReadOnlyTool(name="safe", url="https://example.invalid/mcp/")
        for name in ("register_customer", "order_arepa", "cancel_order", "get_customer"):
            with patch.object(RecordingMCPTool, "call_tool", new_callable=AsyncMock) as transport:
                with self.assertRaises(RuntimeError):
                    asyncio.run(tool.call_tool(name))
                transport.assert_not_awaited()

    def test_pinned_adapter_duplicate_text_and_structured_content(self):
        self.assertEqual(decode_result([
            Content.from_text('[{"name":"Synthetic"}]'),
            Content.from_text('{"result":[{"name":"Synthetic"}]}'),
        ]), [{"name": "Synthetic"}])


if __name__ == "__main__":
    unittest.main()
