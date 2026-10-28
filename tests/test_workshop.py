"""Offline regression for the learner package; no model or service credentials."""

import ast
import asyncio
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import re
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, call, patch, sentinel

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "arepa-agent"
sys.path.insert(0, str(AGENT))

import catering
import receipt
import settings
from jsonschema import ValidationError
from mcp.types import CallToolResult, TextContent

TOOL_ARGUMENTS = {
    "register_customer": ("first_name", "last_name", "city"),
    "get_customer": ("customer_id",),
    "list_arepas": (),
    "order_arepa": ("flavor_id", "customer_id", "kind", "voucher_code"),
    "check_order_status": ("customer_id",),
    "cancel_order": ("customer_id", "kind"),
    "voucher_status": (),
}
ENV = {
    "FOUNDRY_ENDPOINT": "https://example.invalid/anthropic",
    "FOUNDRY_API_KEY": "offline-only",
    "FOUNDRY_MODEL_DEPLOYMENT": "configured-claude",
    "AREPA_MCP_URL": "http://127.0.0.1:8765/mcp/",
    "AZURE_SEARCH_ENDPOINT": "https://example.invalid/",
    "AZURE_SEARCH_QUERY_KEY": "query-only",
    "KNOWLEDGE_BASE_NAME": "cupcake-store-kb",
}


def sources():
    starter = (AGENT / "agent.py").read_text()
    yield "starter", 1, starter
    for stage in range(1, 5):
        yield f"snapshot-{stage}", stage, (
            AGENT / f"snapshots/agent-module-1.{stage}.py"
        ).read_text()
        text = (ROOT / f"lab/module-1.{stage}.md").read_text()
        blocks = dict(re.findall(
            r"<!-- build: (\w+) -->\s*```python\n(.*?)```", text, re.S
        ))
        if set(blocks) != {"imports", "main"}:
            raise AssertionError(f"Missing build blocks in module 1.{stage}")
        base = ast.parse(starter)
        imports = ast.parse(blocks["imports"]).body
        main = ast.parse(blocks["main"]).body
        body = [
            node for node in base.body
            if not isinstance(node, (ast.Import, ast.ImportFrom, ast.AsyncFunctionDef))
        ]
        yield f"assembled-{stage}", stage, ast.unparse(ast.Module(
            body=imports + body + main, type_ignores=[]
        ))


def result(data, *, structured=False, error=False):
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(data))],
        structuredContent=data if structured else None, isError=error,
    )


class ClientTests(unittest.TestCase):
    def run_client(self, source, stage, *, failure=None, inputs=None, endpoint=None):
        environment = {**ENV, **({"FOUNDRY_ENDPOINT": endpoint} if endpoint else {})}
        store = Mock(connect=AsyncMock(), close=AsyncMock(),
                     get_prompt=AsyncMock(side_effect=["server persona", "AREPA LAB"]))
        knowledge = Mock(connect=AsyncMock(), close=AsyncMock())
        agent = Mock(create_session=Mock(return_value=sentinel.session),
                     run=AsyncMock(return_value=SimpleNamespace(
                         messages=[SimpleNamespace(text="before"), SimpleNamespace(text="after")]
                     )))
        if failure == "run":
            agent.run.side_effect = RuntimeError("model failed")
        if failure == "prompt":
            store.get_prompt.side_effect = RuntimeError("prompt failed")
        if failure == "knowledge":
            knowledge.connect.side_effect = RuntimeError("knowledge failed")
        namespace = {"__name__": "offline_agent", "__file__": str(AGENT / "agent.py")}
        with (
            patch.dict(os.environ, environment, clear=True),
            patch("dotenv.load_dotenv") as load,
            patch("agent_framework.Agent", return_value=agent) as factory,
            patch("agent_framework.foundry.AnthropicFoundryClient") as client,
            patch("agent_framework.openai.OpenAIChatClient") as openai,
            patch("agent_framework.MCPStreamableHTTPTool",
                  side_effect=[store, knowledge]) as tools,
            patch("builtins.input", side_effect=inputs or ["", "show menu", "quit"]),
            redirect_stdout(io.StringIO()) as output,
        ):
            exec(compile(source, namespace["__file__"], "exec"), namespace)
            if failure:
                with self.assertRaisesRegex(RuntimeError, "failed"):
                    asyncio.run(namespace["main"]())
            else:
                asyncio.run(namespace["main"]())
            load.assert_called_once_with(ROOT / ".env")
            expected_url = environment["FOUNDRY_ENDPOINT"].rstrip("/")
            is_gpt = "/api/projects/" in expected_url or expected_url.endswith("/openai/v1")
            if "/api/projects/" in expected_url and not expected_url.endswith("/openai/v1"):
                expected_url += "/openai/v1"
            selected = openai if is_gpt else client
            unused = client if is_gpt else openai
            unused.assert_not_called()
            selected.assert_called_once_with(
                model=ENV["FOUNDRY_MODEL_DEPLOYMENT"], api_key=ENV["FOUNDRY_API_KEY"],
                base_url=expected_url,
            )
        return store, knowledge, agent, factory, tools, output.getvalue(), namespace

    def test_all_nine_learning_sources(self):
        variants = list(sources())
        self.assertEqual(len(variants), 9)
        for name, stage, source in variants:
            with self.subTest(source=name):
                store, kb, agent, factory, tools, output, namespace = self.run_client(source, stage)
                self.assertEqual(factory.call_args.kwargs["name"], "arepa-agent")
                self.assertEqual(namespace["reply"](SimpleNamespace(messages=[
                    SimpleNamespace(text="one"), SimpleNamespace(text=""),
                    SimpleNamespace(text="two"),
                ])), "one\n\ntwo")
                if stage == 1:
                    tools.assert_not_called()
                    self.assertNotIn("instructions", factory.call_args.kwargs)
                else:
                    self.assertEqual(tools.call_args_list[0].kwargs["url"], ENV["AREPA_MCP_URL"])
                    store.connect.assert_awaited_once()
                    store.close.assert_awaited_once()
                    self.assertEqual(store.get_prompt.await_args_list, [
                        call("agent_instructions"), call("welcome_banner"),
                    ])
                    self.assertIn("AREPA LAB", output)
                    self.assertEqual(factory.call_args.kwargs["instructions"],
                                     "server persona" + (settings.ROUTING if stage >= 3 else ""))
                    self.assertIsInstance(factory.call_args.kwargs["middleware"][0], settings.ToolTrace)
                if stage >= 3:
                    kb.connect.assert_awaited_once()
                    kb.close.assert_awaited_once()
                    config = tools.call_args_list[1].kwargs
                    self.assertIn("/knowledgebases/cupcake-store-kb/mcp?", config["url"])
                    self.assertFalse(config["load_prompts"])
                    self.assertEqual(config["header_provider"]({}), {"api-key": "query-only"})
                if stage == 4:
                    self.assertIsInstance(
                        tools.call_args_list[0].kwargs["parse_tool_results"].__self__,
                        receipt.OrderCapture,
                    )
                expected = ([call("hello", session=sentinel.session)] if stage >= 2 else [])
                expected += [call("show menu", session=sentinel.session)]
                self.assertEqual(agent.run.await_args_list, expected)

    def test_copy_paste_functions_match_snapshots(self):
        variants = {name: ast.parse(source) for name, _, source in sources()}
        for stage in range(1, 5):
            def main(name):
                return ast.dump(next(n for n in variants[name].body
                                     if isinstance(n, ast.AsyncFunctionDef) and n.name == "main"))
            self.assertEqual(main(f"snapshot-{stage}"), main(f"assembled-{stage}"))

    def test_gpt_paths_use_all_actual_learning_sources(self):
        for name, stage, source in sources():
            for endpoint in (
                "https://example.invalid/openai/v1/",
                "https://example.invalid/api/projects/test-project",
                "https://example.invalid/api/projects/test-project/openai/v1",
            ):
                with self.subTest(source=name, endpoint=endpoint):
                    self.run_client(source, stage, endpoint=endpoint)

    def test_all_connected_tools_close_on_failure(self):
        for name, stage, source in sources():
            if stage < 2:
                continue
            for failure in ("run", "prompt") + (("knowledge",) if stage >= 3 else ()):
                with self.subTest(source=name, failure=failure):
                    store, kb, *_ = self.run_client(source, stage, failure=failure)
                    store.close.assert_awaited_once()
                    if stage >= 3 and failure != "knowledge":
                        kb.close.assert_awaited_once()

    def test_receipt_command_requires_confirmed_data(self):
        source = (AGENT / "snapshots/agent-module-1.4.py").read_text()
        with patch("receipt.make_receipt") as make:
            *_, output, _ = self.run_client(source, 4, inputs=["receipt", "exit"])
        make.assert_not_called()
        self.assertIn("No confirmed order", output)

    def test_trace_exposes_only_tool_name(self):
        output = io.StringIO()
        context = SimpleNamespace(function=SimpleNamespace(name="order_arepa"),
                                  arguments={"voucher_code": "secret", "customer_id": "private"})
        next_call = AsyncMock()
        with redirect_stdout(output):
            asyncio.run(settings.ToolTrace().process(context, next_call))
        self.assertEqual(output.getvalue(), "[tool] order_arepa\n")
        next_call.assert_awaited_once()

    def test_model_configuration_and_endpoint_validation(self):
        with patch.dict(os.environ, ENV, clear=True):
            self.assertEqual(settings.model_settings()["base_url"], ENV["FOUNDRY_ENDPOINT"])
        for endpoint in ("", "<placeholder>", "https://example.invalid/anthropic/v1/messages",
                         "https://example.invalid/api/projects/test/chat/completions"):
            with self.subTest(endpoint=endpoint), patch.dict(os.environ, {
                **ENV, "FOUNDRY_ENDPOINT": endpoint,
            }, clear=True), self.assertRaises(ValueError):
                settings.model_settings()

    def test_documented_contract_and_menu_rubric(self):
        readme = (ROOT / "README.md").read_text()
        documented = {
            name: tuple(p.strip() for p in parameters.split(",") if p.strip())
            for name, parameters in re.findall(r"`(\w+)\(([^)]*)\)`", readme)
            if name in TOOL_ARGUMENTS
        }
        self.assertEqual(documented, TOOL_ARGUMENTS)
        for module in ("1.2", "1.6"):
            text = (ROOT / f"lab/module-{module}.md").read_text()
            for term in ("numbered list", "description", "USD price", "stock_label",
                         "empty menu", "Machine IDs"):
                self.assertIn(term, text)

    def test_environment_and_policy_boundaries(self):
        template = (ROOT / ".env.example").read_text()
        self.assertIn('KNOWLEDGE_BASE_NAME="cupcake-store-kb"', template)
        self.assertIn(
            'AREPA_MCP_URL="https://ca-arepa-mcp.yellowbeach-684b8340.eastus.azurecontainerapps.io/mcp/"',
            template,
        )
        for term in ("fictional", "eligibility", "pending-only", "cannot override",
                     "refund", "deposit", "staff"):
            self.assertIn(term, settings.ROUTING)
        source = (ROOT / "foundry-iq/docs/arepalab-store-info.md").read_text()
        self.assertNotIn("All of our products are Gluten-Free", source)
        self.assertIn("fictional retail scenario", source)
        self.assertIn("pending-only", source)

    def test_relative_document_links(self):
        paths = [ROOT / "README.md", *ROOT.glob("lab/*.md"), *ROOT.glob("tests/**/*.md")]
        for path in paths:
            for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text()):
                if "://" in link or link.startswith("#"):
                    continue
                with self.subTest(path=path.name, link=link):
                    self.assertTrue((path.parent / link.split("#", 1)[0]).exists())

    def test_ingestion_keeps_scope_with_each_retrieved_chunk(self):
        tree = ast.parse((ROOT / "foundry-iq/ingest_foundry_iq.py").read_text())
        nodes = [node for node in tree.body if (
            isinstance(node, ast.FunctionDef) and node.name == "chunk_document"
        ) or (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "SOURCE_SCOPE" for t in node.targets)
        )]
        namespace = {"re": re, "Path": Path}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "<chunking>", "exec"), namespace)
        chunks = namespace["chunk_document"](ROOT / "foundry-iq/docs/arepalab-store-info.md")
        self.assertGreater(len(chunks), 5)
        for chunk in chunks:
            self.assertTrue(chunk["content"].startswith(namespace["SOURCE_SCOPE"]))
            self.assertIn("pending-only", chunk["content"])
        self.assertEqual(len({c["id"] for c in chunks}), len(chunks))

    def test_policy_verifier_root_env_and_cleanup_on_model_error(self):
        namespace = runpy.run_path(str(ROOT / "foundry-iq/verify_knowledge_base.py"))
        agent = Mock(run=AsyncMock(side_effect=RuntimeError("model failed")))
        tool = Mock(connect=AsyncMock(), close=AsyncMock())
        with patch.dict(os.environ, ENV, clear=True), \
             patch.dict(namespace["main"].__globals__, {
                 "build_agent": Mock(return_value=(agent, tool)), "load_dotenv": Mock(),
             }), redirect_stdout(io.StringIO()):
            loader = namespace["main"].__globals__["load_dotenv"]
            with self.assertRaises(RuntimeError):
                asyncio.run(namespace["main"]())
            loader.assert_called_once_with(ROOT / ".env", override=True)
        tool.close.assert_awaited_once()


class ReceiptTests(unittest.TestCase):
    source = {"success": True, "kind": "test", "flavor": "Synthetic Arepa",
              "board_name": "Test P.", "order_id": "internal"}

    def test_order_capture_structured_and_text(self):
        for structured in (False, True):
            capture = receipt.OrderCapture()
            data = result(self.source, structured=structured)
            self.assertEqual(json.loads(capture.parse_result(data)), self.source)
            self.assertEqual(capture.source, {
                "success": True, "kind": "test", "flavor": "Synthetic Arepa",
            })
            self.assertNotIn("order_id", capture.source)

    def test_cancellation_and_registration_clear_capture(self):
        for data in (
            {"success": False, "error_code": "sold_out"},
            {"success": True, "customer_id": "ABCDEFGH", "board_name": "Test P."},
            {"success": True, "kind": "test", "flavor": "Synthetic Arepa",
             "order_id": "internal", "message": "Cancelled"},
        ):
            capture = receipt.OrderCapture()
            capture.parse_result(result(self.source))
            capture.parse_result(result(data, structured=True))
            self.assertIsNone(capture.source)

    def test_error_and_malformed_results_clear_capture(self):
        for bad in (
            result(self.source, error=True),
            CallToolResult(content=[TextContent(type="text", text="not JSON")]),
            CallToolResult(content=[]),
            result({**self.source, "kind": "bulk"}),
        ):
            capture = receipt.OrderCapture()
            capture.parse_result(result(self.source))
            try:
                capture.parse_result(bad)
            except ValueError:
                pass
            self.assertIsNone(capture.source)

    def test_read_only_results_preserve_capture(self):
        capture = receipt.OrderCapture()
        capture.parse_result(result(self.source))
        capture.parse_result(result({"found": True, "can_order_real": False}))
        capture.parse_result(result([]))
        self.assertEqual(capture.source["flavor"], "Synthetic Arepa")

    def test_source_must_be_confirmed_single_counter_item(self):
        for source in ({}, {"success": False}, {**self.source, "kind": "bulk"},
                       {**self.source, "flavor": ""}, {**self.source, "flavor": None}):
            with self.subTest(source=source), self.assertRaises(ValueError):
                receipt.expected_summary(source)

    def test_structured_receipt_equals_confirmed_source(self):
        expected = receipt.expected_summary(self.source)
        with patch("receipt.structured_output", return_value=json.dumps(expected)) as output:
            self.assertEqual(receipt.make_receipt(self.source), expected)
        self.assertEqual(output.call_args.args[1], receipt.RECEIPT_SCHEMA)
        for value in ({**expected, "item": "Invented"}, {**expected, "payment_processed": True},
                      {**expected, "quantity": 2}, {**expected, "order_id": "invented"}, None):
            with patch("receipt.structured_output", return_value=json.dumps(value)):
                with self.assertRaises((ValueError, ValidationError)):
                    receipt.make_receipt(self.source)

    def test_request_receipt_never_confirms_catering_or_payment(self):
        request = json.loads((AGENT / "examples/request.json").read_text())
        checked = receipt.checked_json(json.dumps(request), catering.ORDER_SCHEMA)
        summary = receipt.make_request_receipt(checked)
        self.assertEqual(summary["status"], "requested")
        self.assertIs(summary["payment_processed"], False)
        self.assertEqual(summary["items"], request["items"])


class CateringTests(unittest.TestCase):
    def test_guard_blocks_real_missing_and_invalid_kind(self):
        for arguments in ({"kind": "real"}, {}, {"kind": "TEST"},
                          SimpleNamespace(kind="real")):
            context = SimpleNamespace(function=SimpleNamespace(name="order_arepa"),
                                      arguments=arguments)
            next_call = AsyncMock()
            with self.assertRaises(catering.MiddlewareFailure):
                asyncio.run(catering.TestOrdersOnly().process(context, next_call))
            next_call.assert_not_awaited()

    def test_guard_allows_test_and_read_only_tools(self):
        for name, arguments in (("order_arepa", {"kind": "test"}),
                                ("order_arepa", SimpleNamespace(kind="test")),
                                ("list_arepas", {})):
            next_call = AsyncMock()
            with redirect_stdout(io.StringIO()):
                asyncio.run(catering.TestOrdersOnly().process(SimpleNamespace(
                    function=SimpleNamespace(name=name), arguments=arguments,
                ), next_call))
            next_call.assert_awaited_once()

    def test_vision_uses_supported_image_and_schema_api(self):
        request = json.loads((AGENT / "examples/request.json").read_text())
        with patch("pathlib.Path.read_bytes", return_value=b"synthetic-image"), \
             patch("catering.structured_output", return_value=json.dumps(request)) as output:
            self.assertEqual(catering.read_order(Path("fixture.png")), request)
        self.assertEqual(output.call_args.args[1], catering.ORDER_SCHEMA)
        self.assertEqual(output.call_args.kwargs["image"], ("image/png", "c3ludGhldGljLWltYWdl"))
        with self.assertRaises(ValueError):
            catering.read_order(Path("unsupported.gif"))

    def test_unreviewed_extraction_cannot_act(self):
        with patch("builtins.input", return_value="no"), \
             patch("catering.work_order", new_callable=AsyncMock) as work, \
             redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            asyncio.run(catering.main(None, AGENT / "examples/request.json"))
        work.assert_not_awaited()

    def test_catering_exposes_no_registration_or_cancellation(self):
        tree = ast.parse((AGENT / "catering.py").read_text())
        tools = next(
            keyword.value for node in ast.walk(tree) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name) and node.func.id == "MCPStreamableHTTPTool"
            for keyword in node.keywords if keyword.arg == "allowed_tools"
        )
        self.assertEqual(set(ast.literal_eval(tools)), {
            "get_customer", "list_arepas", "order_arepa", "check_order_status", "voucher_status",
        })


if __name__ == "__main__":
    unittest.main()
