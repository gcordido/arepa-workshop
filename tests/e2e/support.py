"""Disposable HTTP services, adapted from the previous workshop's E2E harness."""

from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time

from agent_framework import MCPStreamableHTTPTool
import httpx

ROOT = Path(__file__).resolve().parents[2]
TOOL_ARGUMENTS = {
    "register_customer": {"first_name", "last_name", "city"},
    "get_customer": {"customer_id"},
    "list_arepas": set(),
    "order_arepa": {"flavor_id", "customer_id", "kind", "voucher_code"},
    "check_order_status": {"customer_id"},
    "cancel_order": {"customer_id", "kind"},
    "voucher_status": set(),
}
FLAVOR_ID = "regression-arepa"
FLAVOR_NAME = "Regression Arepa"
# Azurite's published development credential, never an Azure account secret.
AZURITE_KEY = (
    "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6"
    "tq/K1SZFPTOtr/KBHBeksoGMGw=="
)


def decode_result(result):
    # Core 1.17 appends structured JSON after text; joining both corrupts JSON.
    # The last block is structured data when present, otherwise the text result.
    text = result if isinstance(result, str) else result[-1].text
    value = json.loads(text)
    return value["result"] if isinstance(value, dict) and set(value) == {"result"} else value


class RecordingMCPTool(MCPStreamableHTTPTool):
    """Observe actual adapter calls; do not mock transport or server results."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = []
        self.prompts = []

    async def call_tool(self, tool_name, **kwargs):
        if len(self.calls) >= 100:
            raise RuntimeError("Regression tool-call budget exceeded")
        response = await super().call_tool(tool_name, **kwargs)
        self.calls.append({"tool": tool_name, "result": decode_result(response)})
        return response

    async def call(self, name, **arguments):
        return decode_result(await self.call_tool(name, **arguments))

    async def get_prompt(self, name, *args, **kwargs):
        response = await super().get_prompt(name, *args, **kwargs)
        self.prompts.append(name)
        return response


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def stop_process(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


class LocalServer:
    """Copy only server code, inject local-only storage and discard all state."""

    def __init__(self, label="contract"):
        self.label = label

    def __enter__(self):
        self.stack = ExitStack()
        try:
            self.start()
        except BaseException:
            self.stack.close()
            raise
        return self

    def __exit__(self, *args):
        self.stack.close()

    def start_process(self, name, command, *, env=None, cwd=None):
        log = self.stack.enter_context((self.directory / f"{name}.log").open("w"))
        process = subprocess.Popen(
            command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
        )
        self.stack.callback(stop_process, process)
        return process

    def wait_for_http(self, process, url, expected):
        deadline = time.monotonic() + 45
        with httpx.Client(timeout=1, trust_env=False) as client:
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"Local service exited; see {self.directory}")
                try:
                    response = client.get(url)
                except httpx.TransportError:
                    pass
                else:
                    if response.status_code == expected:
                        return
                time.sleep(0.1)
        raise TimeoutError(f"Local service did not start; see {self.directory}")

    def start(self):
        source = Path(os.environ["AREPA_SERVER_REPO"]).resolve()
        self.python = str(Path(os.environ["AREPA_SERVER_PYTHON"]).absolute())
        if Path(self.python).parent == Path(sys.executable).absolute().parent:
            raise ValueError("Use separate client and server virtual environments.")
        if not (source / "backend/main.py").is_file():
            raise ValueError("AREPA_SERVER_REPO must contain backend/main.py.")
        azurite = os.environ.get("AREPA_AZURITE") or shutil.which("azurite-table")
        if not azurite:
            raise RuntimeError("azurite-table is missing; see tests/e2e/README.md.")
        self.directory = Path(os.environ["AREPA_E2E_ARTIFACTS"]) / self.label
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="arepa-e2e-")))
        self.repo = temporary / "server"
        shutil.copytree(source / "backend", self.repo / "backend",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".env", ".env.*"))
        table_port = free_port()
        table_url = f"http://127.0.0.1:{table_port}/devstoreaccount1"
        storage = self.start_process("azurite", [
            azurite, "--tableHost", "127.0.0.1", "--tablePort", str(table_port),
            "--location", str(temporary / "storage"), "--silent",
        ], cwd=temporary)
        self.wait_for_http(storage, f"{table_url}/Tables", 403)
        self.password = secrets.token_urlsafe(24)
        self.environment = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR")
                            if key in os.environ}
        self.environment.update({
            "AZURE_STORAGE_CONNECTION_STRING": (
                "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
                f"AccountKey={AZURITE_KEY};TableEndpoint={table_url};"
            ),
            "SESSION_SECRET": secrets.token_urlsafe(32),
            "SESSION_COOKIE_SECURE": "false",
            "INITIAL_ADMIN_PASSWORD": self.password,
            "VOUCHER_SECRET": secrets.token_urlsafe(32),
            "WORKSHOP_URL": "",
            "WORKSHOP_TRAINING_KEY": "",
        })
        port = free_port()
        self.url = f"http://127.0.0.1:{port}"
        self.mcp_url = f"{self.url}/mcp/"
        app = self.start_process("server", [
            self.python, "-m", "uvicorn", "backend.main:app",
            "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning",
        ], env=self.environment, cwd=self.repo)
        self.wait_for_http(app, f"{self.url}/arepas", 200)
        self.web = self.stack.enter_context(httpx.Client(
            base_url=self.url, follow_redirects=True, timeout=15, trust_env=False,
        ))
        login = self.post("/admin/login", data={"username": "admin", "password": self.password})
        token = re.search(r'name="csrf-token" content="([^"]+)"', login.text)
        if token is None:
            raise AssertionError("Isolated admin login did not return a CSRF token.")
        self.web.headers["X-CSRF-Token"] = token.group(1)
        self.post("/admin/flavors", data={
            "name": FLAVOR_NAME, "description": "Synthetic integration fixture",
            "price": "6.25", "stock": "12",
        })
        if self.snapshot()["flavors"][0]["RowKey"] != FLAVOR_ID:
            raise AssertionError("Unexpected isolated flavor slug.")

    def post(self, path, **kwargs):
        response = self.web.post(path, **kwargs)
        response.raise_for_status()
        return response

    def voucher(self, window_offset=0):
        # Derive a deterministic current/expired code using only the disposable secret.
        completed = subprocess.run([
            self.python, "-c",
            "from backend import voucher; import time; "
            f"print(voucher._code_for_window(int(time.time()) // voucher.WINDOW_SECONDS + {window_offset}))",
        ], cwd=self.repo, env=self.environment, capture_output=True, text=True, check=True, timeout=20)
        return completed.stdout.strip()

    def set_stock(self, stock):
        self.post(f"/admin/flavors/{FLAVOR_ID}/edit", data={"stock": str(stock)})

    def snapshot(self):
        completed = subprocess.run([
            self.python, "-c",
            "import json; from backend import storage; "
            "print(json.dumps({'flavors': storage.list_flavors(), "
            "'orders': storage.list_orders(), 'customers': storage.list_customers()}, default=str))",
        ], cwd=self.repo, env=self.environment, capture_output=True, text=True, check=True, timeout=20)
        return json.loads(completed.stdout)
