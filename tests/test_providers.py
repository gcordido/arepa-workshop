"""Provider compatibility checks without model calls or credentials."""

import json
import os
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "arepa-agent"))
import catering
import receipt
import settings


def environment(provider):
    return {
        "FOUNDRY_ENDPOINT": (
            "https://example.invalid/anthropic" if provider == "anthropic"
            else "https://example.invalid/api/projects/test-project"
        ),
        "FOUNDRY_API_KEY": "offline-only",
        "FOUNDRY_MODEL_DEPLOYMENT": "configured-model",
        "AZURE_SEARCH_ENDPOINT": "https://search.invalid",
        "AZURE_SEARCH_QUERY_KEY": "offline-query",
    }


def response(provider, text):
    if provider == "anthropic":
        return SimpleNamespace(stop_reason="end_turn", content=[
            SimpleNamespace(type="thinking"),
            SimpleNamespace(type="text", text=text),
        ])
    return SimpleNamespace(choices=[SimpleNamespace(
        finish_reason="stop", message=SimpleNamespace(content=text, refusal=None),
    )])


class ProviderTests(unittest.TestCase):
    def test_endpoint_normalization(self):
        for endpoint, expected in (
            ("https://example.invalid/anthropic/", "https://example.invalid/anthropic"),
            ("https://example.invalid/openai/v1/", "https://example.invalid/openai/v1"),
            ("https://example.invalid/api/projects/test-project",
             "https://example.invalid/api/projects/test-project/openai/v1"),
            ("https://example.invalid/api/projects/test-project/openai/v1",
             "https://example.invalid/api/projects/test-project/openai/v1"),
        ):
            with self.subTest(endpoint=endpoint), patch.dict(os.environ, {
                **environment("anthropic"), "FOUNDRY_ENDPOINT": endpoint,
            }, clear=True):
                self.assertEqual(settings.model_settings()["base_url"], expected)

    def test_structured_schema_and_image_shapes_for_both_providers(self):
        schema = receipt.RECEIPT_SCHEMA
        for provider, target in (("anthropic", "anthropic.AnthropicFoundry"),
                                 ("openai", "openai.OpenAI")):
            with self.subTest(provider=provider), patch.dict(os.environ, environment(provider), clear=True), \
                 patch(target) as factory:
                client = factory.return_value.__enter__.return_value
                create = client.messages.create if provider == "anthropic" else client.chat.completions.create
                create.return_value = response(provider, '{"ok":true}')
                self.assertEqual(settings.structured_output(
                    "extract", schema, max_tokens=1200, image=("image/png", "aW1hZ2U="),
                ), '{"ok":true}')
                arguments = create.call_args.kwargs
                self.assertEqual(arguments["model"], "configured-model")
                if provider == "anthropic":
                    self.assertEqual(arguments["max_tokens"], 1200)
                    self.assertEqual(arguments["output_config"]["format"]["schema"], schema)
                    self.assertEqual(arguments["messages"][0]["content"][0], {
                        "type": "image", "source": {
                            "type": "base64", "media_type": "image/png", "data": "aW1hZ2U=",
                        },
                    })
                else:
                    self.assertEqual(arguments["response_format"]["json_schema"]["schema"], schema)
                    self.assertIs(arguments["response_format"]["json_schema"]["strict"], True)
                    self.assertGreaterEqual(arguments["max_completion_tokens"], 1200)
                    self.assertEqual(arguments["messages"][0]["content"][0], {
                        "type": "image_url", "image_url": {"url": "data:image/png;base64,aW1hZ2U="},
                    })
                factory.return_value.__exit__.assert_called_once()

    def test_no_text_is_never_accepted(self):
        for provider, target in (("anthropic", "anthropic.AnthropicFoundry"),
                                 ("openai", "openai.OpenAI")):
            with self.subTest(provider=provider), patch.dict(os.environ, environment(provider), clear=True), \
                 patch(target) as factory:
                client = factory.return_value.__enter__.return_value
                create = client.messages.create if provider == "anthropic" else client.chat.completions.create
                create.return_value = response(provider, "")
                with self.assertRaisesRegex(ValueError, "no text"):
                    settings.structured_output("extract", {}, max_tokens=500)

    def test_openai_refusals_truncation_and_missing_choices_fail_explicitly(self):
        outcomes = [
            SimpleNamespace(choices=[]),
            SimpleNamespace(choices=[SimpleNamespace(
                finish_reason="length", message=SimpleNamespace(content="{}", refusal=None),
            )]),
            SimpleNamespace(choices=[SimpleNamespace(
                finish_reason="stop", message=SimpleNamespace(content="{}", refusal="refused"),
            )]),
        ]
        with patch.dict(os.environ, environment("openai"), clear=True), patch("openai.OpenAI") as factory:
            create = factory.return_value.__enter__.return_value.chat.completions.create
            for outcome in outcomes:
                create.return_value = outcome
                with self.assertRaises(ValueError):
                    settings.structured_output("extract", {}, max_tokens=500)

    def test_anthropic_refusal_and_truncation_fail_explicitly(self):
        with patch.dict(os.environ, environment("anthropic"), clear=True), \
             patch("anthropic.AnthropicFoundry") as factory:
            create = factory.return_value.__enter__.return_value.messages.create
            for reason in ("max_tokens", "refusal"):
                outcome = response("anthropic", "{}")
                outcome.stop_reason = reason
                create.return_value = outcome
                with self.assertRaises(ValueError):
                    settings.structured_output("extract", {}, max_tokens=500)

    def test_sdk_errors_propagate_and_clients_close(self):
        for provider, target in (("anthropic", "anthropic.AnthropicFoundry"),
                                 ("openai", "openai.OpenAI")):
            with self.subTest(provider=provider), patch.dict(os.environ, environment(provider), clear=True), \
                 patch(target) as factory:
                client = factory.return_value.__enter__.return_value
                create = client.messages.create if provider == "anthropic" else client.chat.completions.create
                create.side_effect = RuntimeError("model failed")
                with self.assertRaisesRegex(RuntimeError, "model failed"):
                    settings.structured_output("extract", {}, max_tokens=500)
                factory.return_value.__exit__.assert_called_once()

    def test_real_receipt_path_checks_source_values_for_both_providers(self):
        expected = receipt.expected_summary(receipt.SAMPLE_RESULT)
        for provider, target in (("anthropic", "anthropic.AnthropicFoundry"),
                                 ("openai", "openai.OpenAI")):
            with self.subTest(provider=provider), patch.dict(os.environ, environment(provider), clear=True), \
                 patch(target) as factory:
                client = factory.return_value.__enter__.return_value
                create = client.messages.create if provider == "anthropic" else client.chat.completions.create
                create.return_value = response(provider, json.dumps(expected))
                self.assertEqual(receipt.make_receipt(receipt.SAMPLE_RESULT), expected)
                create.return_value = response(provider, json.dumps({**expected, "item": "Invented"}))
                with self.assertRaisesRegex(ValueError, "disagrees"):
                    receipt.make_receipt(receipt.SAMPLE_RESULT)

    def test_real_vision_path_validates_both_provider_outputs(self):
        request = json.loads((ROOT / "arepa-agent/examples/request.json").read_text())
        for provider, target in (("anthropic", "anthropic.AnthropicFoundry"),
                                 ("openai", "openai.OpenAI")):
            with self.subTest(provider=provider), patch.dict(os.environ, environment(provider), clear=True), \
                 patch(target) as factory, patch("pathlib.Path.read_bytes", return_value=b"synthetic-image"):
                client = factory.return_value.__enter__.return_value
                create = client.messages.create if provider == "anthropic" else client.chat.completions.create
                create.return_value = response(provider, json.dumps(request))
                self.assertEqual(catering.read_order(Path("fixture.jpg")), request)

    def test_iq_verifier_uses_shared_chat_client(self):
        namespace = runpy.run_path(str(ROOT / "foundry-iq/verify_knowledge_base.py"))
        with patch.dict(os.environ, environment("openai"), clear=True), patch.dict(
            namespace["build_agent"].__globals__, {"create_chat_client": Mock(return_value=Mock())},
        ):
            _, tool = namespace["build_agent"]()
            namespace["build_agent"].__globals__["create_chat_client"].assert_called_once()
            self.assertIn("/knowledgebases/cupcake-store-kb/mcp?", tool.url)


if __name__ == "__main__":
    unittest.main()
