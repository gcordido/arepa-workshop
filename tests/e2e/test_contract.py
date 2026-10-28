"""Real client adapter -> isolated HTTP MCP server -> disposable Azure Tables."""

import unittest
import sys

from support import FLAVOR_ID, FLAVOR_NAME, LocalServer, RecordingMCPTool, ROOT, TOOL_ARGUMENTS

sys.path.insert(0, str(ROOT / "arepa-agent"))
from receipt import OrderCapture


class ContractTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = cls.enterClassContext(LocalServer())

    async def asyncSetUp(self):
        self.server.set_stock(12)
        self.tool = RecordingMCPTool(name="regression", url=self.server.mcp_url)
        await self.tool.connect()
        self.addAsyncCleanup(self.tool.close)

    async def customer(self):
        result = await self.tool.call(
            "register_customer", first_name="Synthetic", last_name="Tester", city="Test City",
        )
        self.assertTrue(result["success"])
        return result["customer_id"]

    async def order(self, registered_id, kind="real", **overrides):
        return await self.tool.call("order_arepa", **{
            "flavor_id": FLAVOR_ID, "customer_id": registered_id, "kind": kind,
            "voucher_code": self.server.voucher(), **overrides,
        })

    def state(self, customer_id):
        state = self.server.snapshot()
        customer = next(c for c in state["customers"] if c["RowKey"] == customer_id)
        return (state["flavors"][0]["stock"], customer["real_orders_count"],
                [o for o in state["orders"] if o["customer_id"] == customer_id])

    async def test_discovery_seven_tools_and_both_prompts(self):
        tools = (await self.tool.session.list_tools()).tools
        self.assertEqual({tool.name for tool in tools}, set(TOOL_ARGUMENTS))
        reads = {"get_customer", "list_arepas", "check_order_status", "voucher_status"}
        for tool in tools:
            self.assertEqual(set(tool.inputSchema["properties"]), TOOL_ARGUMENTS[tool.name])
            self.assertEqual(set(tool.inputSchema.get("required", [])), TOOL_ARGUMENTS[tool.name])
            self.assertEqual(tool.annotations.readOnlyHint, tool.name in reads)
            self.assertEqual(tool.annotations.destructiveHint,
                             tool.name in {"order_arepa", "cancel_order"})
        self.assertEqual({p.name for p in (await self.tool.session.list_prompts()).prompts},
                         {"agent_instructions", "welcome_banner"})
        self.assertIn("CONVERSATION FLOW", await self.tool.get_prompt("agent_instructions"))
        self.assertIn("AREPA LAB", await self.tool.get_prompt("welcome_banner"))

    async def test_all_seven_tools_test_and_real_cancellation(self):
        customer_id = await self.customer()
        returning = await self.tool.call("get_customer", customer_id=customer_id.lower())
        self.assertTrue(returning["found"])
        self.assertTrue(returning["can_order_real"])
        self.assertIsNone(returning["active_real_order"])
        menu = await self.tool.call("list_arepas")
        self.assertEqual(menu[0], {
            "id": FLAVOR_ID, "name": FLAVOR_NAME, "description": "Synthetic integration fixture",
            "price": 6.25, "stock_status": "plenty", "stock_label": "Plenty available",
        })
        timing = await self.tool.call("voucher_status")
        self.assertEqual(set(timing), {"seconds_until_rotation", "window_seconds", "message"})
        self.assertGreater(timing["seconds_until_rotation"], 0)
        self.assertLessEqual(timing["seconds_until_rotation"], timing["window_seconds"])
        self.assertFalse((await self.tool.call("check_order_status", customer_id=customer_id))["found"])
        self.assertTrue((await self.order(customer_id, "test"))["success"])
        stock, allowance, orders = self.state(customer_id)
        self.assertEqual((stock, allowance, orders[0]["status"]), (12, 0, "collected"))
        self.assertFalse((await self.tool.call("check_order_status", customer_id=customer_id))["found"])
        real = await self.order(customer_id)
        self.assertTrue(real["success"])
        self.assertEqual(self.state(customer_id)[:2], (11, 1))
        self.assertEqual((await self.order(customer_id))["error_code"], "active_order_exists")
        self.assertEqual((await self.tool.call("check_order_status", customer_id=customer_id))["status"], "pending")
        self.assertFalse((await self.tool.call("get_customer", customer_id=customer_id))["can_order_real"])
        self.assertTrue((await self.tool.call("cancel_order", customer_id=customer_id, kind="real"))["success"])
        self.assertEqual(self.state(customer_id)[:2], (12, 0))
        self.assertEqual((await self.tool.call("cancel_order", customer_id=customer_id,
                                               kind="real"))["error_code"], "no_active_order")
        self.assertEqual(self.state(customer_id)[:2], (12, 0))
        self.assertTrue((await self.order(customer_id))["success"])
        self.assertEqual({c["tool"] for c in self.tool.calls}, set(TOOL_ARGUMENTS))

    async def test_ready_collection_and_lifetime_allowance(self):
        customer_id = await self.customer()
        order = await self.order(customer_id)
        self.server.post(f"/admin/orders/{order['order_id']}/ready")
        self.assertEqual((await self.tool.call("check_order_status", customer_id=customer_id))["status"], "ready")
        self.assertEqual((await self.tool.call("cancel_order", customer_id=customer_id,
                                               kind="real"))["error_code"], "order_not_cancellable")
        self.assertEqual(self.state(customer_id)[:2], (11, 1))
        self.server.post(f"/admin/orders/{order['order_id']}/collected")
        self.assertFalse((await self.tool.call("check_order_status", customer_id=customer_id))["found"])
        self.assertEqual((await self.order(customer_id))["error_code"], "real_limit_reached")
        self.assertTrue((await self.order(customer_id, "test"))["success"])
        self.assertEqual(self.state(customer_id)[:2], (11, 1))

    async def test_invalid_inputs_have_no_storage_effect(self):
        before = self.server.snapshot()
        registration = await self.tool.call("register_customer", first_name=" ",
                                            last_name="Invalid@", city="<script>")
        self.assertFalse(registration["success"])
        self.assertEqual(registration["error_code"], "invalid_input")
        self.assertEqual(set(registration["fields"]), {"first_name", "last_name", "city"})
        self.assertEqual(self.server.snapshot(), before)
        customer_id = await self.customer()
        for arguments, code in (
            ({"customer_id": "bad"}, "invalid_input"),
            ({"customer_id": "ZZZZZZZZ"}, "unknown_customer"),
            ({"flavor_id": "not-a-menu-item"}, "flavor_not_found"),
            ({"voucher_code": "WRONG0"}, "malformed_voucher"),
            ({"voucher_code": ""}, "invalid_input"),
        ):
            with self.subTest(arguments=arguments):
                result = await self.order(customer_id, **arguments)
                self.assertEqual((result["success"], result["error_code"]), (False, code))
        self.assertEqual(self.state(customer_id), (12, 0, []))
        for identity, code in (("bad", "invalid_input"), ("ZZZZZZZZ", "unknown_customer")):
            result = await self.tool.call("get_customer", customer_id=identity)
            self.assertEqual((result["found"], result["error_code"]), (False, code))

    async def test_real_adapter_receipt_capture_clears_after_cancellation(self):
        capture = OrderCapture()
        self.tool.parse_tool_results = capture.parse_result
        customer_id = await self.customer()
        self.assertIsNone(capture.source)
        accepted = await self.order(customer_id)
        self.assertTrue(accepted["success"])
        self.assertEqual(capture.source, {
            "success": True, "kind": "real", "flavor": FLAVOR_NAME,
        })
        cancelled = await self.tool.call("cancel_order", customer_id=customer_id, kind="real")
        self.assertTrue(cancelled["success"])
        self.assertIsNone(capture.source)
        self.assertEqual(self.state(customer_id)[:2], (12, 0))

    async def test_stock_thresholds_empty_menu_and_sold_out(self):
        customer_id = await self.customer()
        for stock, status in ((1, "almost_finished"), (3, "almost_finished"),
                              (4, "limited"), (10, "limited"), (11, "plenty")):
            self.server.set_stock(stock)
            self.assertEqual((await self.tool.call("list_arepas"))[0]["stock_status"], status)
        self.server.set_stock(0)
        self.assertEqual(await self.tool.call("list_arepas"), [])
        self.assertEqual((await self.order(customer_id))["error_code"], "sold_out")
        stock, allowance, orders = self.state(customer_id)
        self.assertEqual((stock, allowance), (0, 0))
        self.assertTrue(all(o["status"] == "cancelled" for o in orders))

    async def test_malformed_vouchers_do_not_lock_out_and_grace_window_works(self):
        customer_id = await self.customer()
        for _ in range(11):
            malformed = await self.order(customer_id, "test", voucher_code="WRONG0")
            self.assertEqual(malformed["error_code"], "malformed_voucher")
            self.assertEqual(malformed["invalid_characters"], ["O", "0"])
        self.assertTrue((await self.order(customer_id, "test",
                                        voucher_code=self.server.voucher(-1)))["success"])
        self.assertEqual(self.state(customer_id)[:2], (12, 0))

    async def test_expired_vouchers_lockout_and_cooldown(self):
        customer_id = await self.customer()
        expired = self.server.voucher(-3)
        for _ in range(10):
            wrong = await self.order(customer_id, "test", voucher_code=expired)
            self.assertEqual(wrong["error_code"], "invalid_voucher")
            self.assertGreater(wrong["seconds_until_rotation"], 0)
            self.assertNotIn(wrong["agent_note"], wrong["message"])
        locked = await self.order(customer_id, "test")
        self.assertEqual(locked["error_code"], "voucher_locked")
        self.assertGreater(locked["retry_after_s"], 0)
        self.assertLessEqual(locked["retry_after_s"], 60)
        self.assertEqual(self.state(customer_id), (12, 0, []))
