#!/usr/bin/env python3
# {{ ansible_managed }}
"""Check the NAU MCP server the way an agent uses it, and say what happened at every step.

    make smoke                                   # on the VM, as root, in the folder of the deploy: it reads secrets/agent-token
    read -rsp 'NAU MCP token: ' NAU_MCP_TOKEN; export NAU_MCP_TOKEN
    python3 smoke.py [URL]                       # from a workstation, through the SSH tunnel

URL defaults to http://127.0.0.1:8443/mcp. The token comes from the environment variable NAU_MCP_TOKEN, or from the file
named by NAU_MCP_TOKEN_FILE; never from the command line, where the shell history and `ps` would keep it. It is never
printed. Standard library only, so it runs on the VM and on any workstation with Python 3.8 or later.

The steps: a call without the token is refused (401); the handshake; the list of tools, all marked read-only; and one read
from Grafana (`list_datasources`), which proves that the server reaches its Grafana with its Viewer token. It changes
nothing.
"""

from __future__ import annotations

import http.client
import json
import os
import sys
import urllib.parse

DEFAULT_URL = "http://127.0.0.1:8443/mcp"
PROTOCOL_VERSION = "2025-06-18"
TIMEOUT_S = 30
MAX_BODY = 2_000_000


class SmokeError(Exception):
    pass


def printable(text: object, limit: int = 300) -> str:
    """Remote text, made safe to print: control characters out, length capped."""
    text = "".join(c if c.isprintable() else " " for c in str(text))
    return text if len(text) <= limit else text[:limit] + "..."


def read_token() -> str:
    token = os.environ.get("NAU_MCP_TOKEN", "").strip()
    path = os.environ.get("NAU_MCP_TOKEN_FILE", "")
    if not token and path:
        try:
            with open(path, encoding="utf-8") as f:
                token = f.read().strip()
        except OSError as e:
            raise SmokeError(f"cannot read the token file {path}: {e.strerror} (on the VM, run `make smoke` as root)")
    if not token:
        raise SmokeError(
            "no token: export NAU_MCP_TOKEN (read -rsp 'NAU MCP token: ' NAU_MCP_TOKEN), or set NAU_MCP_TOKEN_FILE"
        )
    return token


def messages(content_type: str, body: str) -> list:
    """The JSON-RPC messages of an answer, whether the server replied with JSON or with an event stream."""
    if content_type.startswith("text/event-stream"):
        chunks, data = [], []
        for line in body.splitlines() + [""]:
            if line.startswith("data:"):
                data.append(line[5:].lstrip(" "))
            elif line == "" and data:
                chunks.append("\n".join(data))
                data = []
    else:
        chunks = [body]
    found = []
    for chunk in chunks:
        try:
            message = json.loads(chunk)
        except ValueError:
            continue
        found += message if isinstance(message, list) else [message]
    return [m for m in found if isinstance(m, dict)]


class Client:
    def __init__(self, url: str, token: str | None):
        self.url = urllib.parse.urlsplit(url)
        if self.url.scheme not in ("http", "https") or not self.url.hostname:
            raise SmokeError(f"not an http(s) URL: {printable(url)}")
        try:
            self.url.port
        except ValueError:
            raise SmokeError(f"not a valid port in the URL: {printable(url)}")
        self.token = token
        self.session: str | None = None
        self.next_id = 0

    def post(self, payload: dict, with_token: bool = True) -> tuple:
        if self.url.scheme == "https":
            connection = http.client.HTTPSConnection(self.url.hostname, self.url.port, timeout=TIMEOUT_S)
        else:
            connection = http.client.HTTPConnection(self.url.hostname, self.url.port, timeout=TIMEOUT_S)
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if with_token and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        try:
            connection.request("POST", self.url.path or "/", body=json.dumps(payload).encode(), headers=headers)
            response = connection.getresponse()
            body = response.read(MAX_BODY).decode("utf-8", "replace")
        except ConnectionRefusedError:
            raise SmokeError(
                f"nothing listens on {self.url.netloc}: is the SSH tunnel open, and is the container up"
                " (`make status` on the VM)?"
            )
        except OSError as e:
            raise SmokeError(f"cannot reach {self.url.netloc}: {printable(e)}")
        except http.client.HTTPException as e:
            raise SmokeError(
                f"{self.url.netloc} did not answer in HTTP ({type(e).__name__}: {printable(e, 120).strip()}):"
                " does the tunnel lead to the port of the server?"
            )
        finally:
            connection.close()
        self.session = response.getheader("Mcp-Session-Id") or self.session
        return response.status, response.getheader("Content-Type") or "", body

    def rpc(self, method: str, params: dict | None = None) -> dict:
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params or {}}
        status, content_type, body = self.post(payload)
        if status == 401:
            raise SmokeError("401: the server refused the token. It must be the agent token of this environment")
        if status == 403:
            raise SmokeError(
                f"403: {printable(body, 120)}. Use http://127.0.0.1:<port>/mcp, with the same local port as on the VM"
            )
        if status != 200:
            raise SmokeError(f"{method}: HTTP {status}: {printable(body)}")
        for message in messages(content_type, body):
            if message.get("id") == self.next_id:
                if "error" in message:
                    error = message["error"]
                    raise SmokeError(f"{method}: {printable(error.get('message', error) if isinstance(error, dict) else error)}")
                return message.get("result") or {}
        raise SmokeError(f"{method}: the answer is not an MCP message: {printable(body, 120)}")

    def notify(self, method: str) -> None:
        self.post({"jsonrpc": "2.0", "method": method})


def step(title: str) -> None:
    print(f"- {title}: ", end="", flush=True)


def run(url: str) -> None:
    token = read_token()

    step("a call without the token is refused")
    status, _, _ = Client(url, None).post(
        {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}}, with_token=False
    )
    if status != 401:
        raise SmokeError(f"expected 401, got {status}: the server must not answer callers without the token")
    print("OK (401)")

    client = Client(url, token)
    step("handshake")
    result = client.rpc(
        "initialize",
        {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "nau-mcp-smoke", "version": "1"}},
    )
    server = result.get("serverInfo") or {}
    print(
        f"OK ({printable(server.get('name'), 40)} {printable(server.get('version'), 20)},"
        f" protocol {printable(result.get('protocolVersion'), 20)})"
    )
    client.notify("notifications/initialized")

    step("tools")
    tools = client.rpc("tools/list").get("tools") or []
    if not tools:
        raise SmokeError("the server lists no tools")
    writable = sorted(t.get("name", "?") for t in tools if not (t.get("annotations") or {}).get("readOnlyHint"))
    if writable:
        raise SmokeError(f"{len(writable)} tool(s) are not marked read-only: {printable(', '.join(writable))}")
    print(f"OK ({len(tools)}, all marked read-only)")

    step("Grafana answers (list_datasources)")
    result = client.rpc("tools/call", {"name": "list_datasources", "arguments": {}})
    text = " ".join(c.get("text", "") for c in result.get("content") or [] if c.get("type") == "text")
    if result.get("isError"):
        raise SmokeError(
            f"the server is up, but it cannot read its Grafana: {printable(text)}. Check that the VM reaches the Grafana"
            " URL (`make status` shows it; a balancer allow-list?) and that the token in secrets/grafana-token is valid"
        )
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    sources = data.get("datasources", data) if isinstance(data, dict) else data
    if isinstance(sources, list):
        kinds = sorted({str(s.get("type")) for s in sources if isinstance(s, dict)})
        print(f"OK ({len(sources)} data source(s): {printable(', '.join(kinds), 200)})")
    else:
        print(f"OK ({printable(text, 120)})")


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    if url in ("-h", "--help"):
        print(__doc__)
        return 0
    print(f"NAU MCP smoke check of {printable(url, 120)}")
    try:
        run(url)
    except SmokeError as e:
        print(f"FAILED\n  {e}")
        return 1
    print("Everything looks: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
