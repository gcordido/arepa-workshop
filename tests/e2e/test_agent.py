"""Actual completed client and configured model; all writes are disposable."""

import asyncio
from contextlib import redirect_stdout
import io
import json
import os
import runpy
import sys
import unittest
from unittest.mock import patch

from support import FLAVOR_NAME, LocalServer, RecordingMCPTool, ROOT, TOOL_ARGUMENTS

sys.path.insert(0, str(ROOT / "arepa-agent"))
from receipt import expected_summary, make_receipt, SAMPLE_RESULT


class AgentJourneyTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = cls.enterClassContext(LocalServer("agent"))

    async def test_model_structured_receipt_matches_simulated_source(self):
        summary = await asyncio.to_thread(make_receipt, SAMPLE_RESULT)
        self.assertEqual(summary, expected_summary(SAMPLE_RESULT))
        (self.server.directory / "model-receipt.json").write_text(json.dumps({
            "model_deployment": os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
            "simulated_source": True, "live_order_created": False,
            "summary": summary,
        }, indent=2) + "\n")

    async def test_actual_client_model_drives_all_seven_tools(self):
        instances = []
        output = io.StringIO()
        completed = False
        turns = 0

        class ObservedTool(RecordingMCPTool):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                instances.append(self)

        def calls():
            self.assertEqual(len(instances), 1)
            return instances[0].calls

        def called(name, start, flag=None, expected=True):
            matching = [c["result"] for c in calls()[start:] if c["tool"] == name]
            if flag is not None:
                matching = [value for value in matching if value.get(flag) is expected]
            self.assertTrue(matching, f"Missing expected {name} call after turn {turns}")
            return matching[-1]

        def state(customer_id, stock, allowance):
            snapshot = self.server.snapshot()
            customer = next(c for c in snapshot["customers"] if c["RowKey"] == customer_id)
            self.assertEqual((snapshot["flavors"][0]["stock"], customer["real_orders_count"]),
                             (stock, allowance))

        def order_message(kind, code):
            return (
                f"I explicitly authorize one {kind} order of {FLAVOR_NAME}. "
                f"The dashboard voucher I read is {code}. Use my existing customer ID."
            )

        def conversation():
            start = len(calls())
            yield ("I am new and have no customer ID. My first name is Synthetic, "
                   "last name is Tester, city is Test City. Please register me.")
            registration = called("register_customer", start, "success")
            customer_id = registration["customer_id"]
            state(customer_id, 12, 0)

            start = len(calls())
            yield "Please refresh and show the current menu. Do not order anything."
            called("list_arepas", start)

            start = len(calls())
            yield order_message("test", self.server.voucher(-3))
            self.assertEqual(called("order_arepa", start, "success", False)["error_code"],
                             "invalid_voucher")
            state(customer_id, 12, 0)

            start = len(calls())
            yield "Check the voucher rotation timing using voucher_status. Do not order yet."
            called("voucher_status", start)

            start = len(calls())
            yield order_message("test", self.server.voucher())
            called("order_arepa", start, "success")
            state(customer_id, 12, 0)

            start = len(calls())
            yield order_message("real", self.server.voucher())
            called("order_arepa", start, "success")
            state(customer_id, 11, 1)

            start = len(calls())
            yield "Please check my active real order status now."
            self.assertEqual(called("check_order_status", start, "found")["status"], "pending")

            start = len(calls())
            yield "I changed my mind. Please cancel my pending real order."
            called("cancel_order", start, "success")
            state(customer_id, 12, 0)

            start = len(calls())
            yield order_message("real", self.server.voucher())
            replacement = called("order_arepa", start, "success")
            state(customer_id, 11, 1)
            self.server.post(f"/admin/orders/{replacement['order_id']}/ready")

            start = len(calls())
            yield "Please check the status of my replacement real order now."
            self.assertEqual(called("check_order_status", start, "found")["status"], "ready")
            self.server.post(f"/admin/orders/{replacement['order_id']}/collected")

            start = len(calls())
            yield "Staff handed me my food. Please check if I still have an active real order."
            called("check_order_status", start, "found", False)

            start = len(calls())
            yield (f"I am returning with customer ID {customer_id}. "
                   "Use get_customer to check my current real-order eligibility.")
            returning = called("get_customer", start, "found")
            self.assertFalse(returning["can_order_real"])
            self.assertIsNone(returning["active_real_order"])
            state(customer_id, 11, 1)
            self.assertEqual({c["tool"] for c in calls()}, set(TOOL_ARGUMENTS))
            self.assertEqual(sum(c["tool"] == "register_customer" for c in calls()), 1)
            snapshot = self.server.snapshot()
            rows = [o for o in snapshot["orders"] if o["customer_id"] == customer_id]
            self.assertEqual(len(rows), 3)
            self.assertCountEqual([row["status"] for row in rows],
                                  ["collected", "cancelled", "collected"])

        script = conversation()

        def user_input(_):
            nonlocal completed, turns
            try:
                message = next(script)
            except StopIteration:
                completed = True
                return "exit"
            turns += 1
            return message

        namespace = runpy.run_path(str(ROOT / "arepa-agent/snapshots/agent-module-1.2.py"))
        main = namespace["main"]
        main.__globals__["MCPStreamableHTTPTool"] = ObservedTool
        try:
            with patch.dict(os.environ, {"AREPA_MCP_URL": self.server.mcp_url}), \
                 patch("builtins.input", side_effect=user_input), redirect_stdout(output):
                await asyncio.wait_for(main(), timeout=300)
            self.assertTrue(completed)
            self.assertEqual(instances[0].prompts, ["agent_instructions", "welcome_banner"])
            self.assertFalse(instances[0].is_connected)
        finally:
            for instance in instances:
                if instance.is_connected:
                    await instance.close()
            (self.server.directory / "model-journey.json").write_text(json.dumps({
                "model_deployment": os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
                "completed": completed, "turns": turns,
                "tool_calls": [c["tool"] for instance in instances for c in instance.calls],
                "transcript": output.getvalue(),
            }, indent=2) + "\n")
