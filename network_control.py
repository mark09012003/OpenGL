"""Small authenticated LAN control channel for master/slave operation."""
from __future__ import annotations

import hmac
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MAX_BODY_BYTES = 4096


def normalize_endpoint(value: str, default_port: int = 8765) -> str:
    value = value.strip().rstrip("/")
    if not value:
        raise ValueError("Slave 位址不可為空")
    if "://" not in value:
        value = "http://" + value
    host_part = value.split("://", 1)[1]
    if ":" not in host_part:
        value += f":{default_port}"
    return value


def local_ip_address() -> str:
    """Return the LAN address without sending application data."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class SlaveControlServer:
    def __init__(self, port, token, status_callback, command_callback,
                 host="0.0.0.0", logger=None):
        self.host = host
        self.port = int(port)
        self.token = str(token)
        self.status_callback = status_callback
        self.command_callback = command_callback
        self.logger = logger
        self._server = None
        self._thread = None

    @property
    def is_running(self):
        return self._server is not None

    def start(self):
        if self.is_running:
            return
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                return

            def _authorized(self):
                supplied = self.headers.get("Authorization", "")
                expected = "Bearer " + owner.token
                return bool(owner.token) and hmac.compare_digest(supplied, expected)

            def _reply(self, code, payload):
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path != "/status":
                    self._reply(404, {"ok": False, "error": "not_found"})
                elif not self._authorized():
                    self._reply(401, {"ok": False, "error": "unauthorized"})
                else:
                    self._reply(200, {"ok": True, **owner.status_callback()})

            def do_POST(self):
                if self.path != "/command":
                    self._reply(404, {"ok": False, "error": "not_found"})
                    return
                if not self._authorized():
                    self._reply(401, {"ok": False, "error": "unauthorized"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 1 or length > MAX_BODY_BYTES:
                        raise ValueError("invalid body size")
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    command = payload.get("command")
                    if command not in ("start", "stop"):
                        raise ValueError("invalid command")
                    owner.command_callback(command)
                    self._reply(202, {"ok": True, "accepted": command})
                except (ValueError, json.JSONDecodeError):
                    self._reply(400, {"ok": False, "error": "bad_request"})

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self.port = self._server.server_address[1]
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever,
                                        name="slave-control", daemon=True)
        self._thread.start()

    def stop(self):
        server = self._server
        self._server = None
        if server is not None:
            server.shutdown()
            server.server_close()
        self._thread = None


class MasterClient:
    def __init__(self, token, timeout=2.0):
        self.token = str(token)
        self.timeout = float(timeout)

    def _request(self, endpoint, path, data=None):
        url = normalize_endpoint(endpoint) + path
        body = None if data is None else json.dumps(data).encode("utf-8")
        request = Request(url, data=body, method="GET" if body is None else "POST",
                          headers={"Authorization": "Bearer " + self.token,
                                   "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 401:
                raise ConnectionError("共享密鑰錯誤") from exc
            raise ConnectionError(f"HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ConnectionError("無法連線") from exc

    def status(self, endpoint):
        return self._request(endpoint, "/status")

    def command(self, endpoint, command):
        if command not in ("start", "stop"):
            raise ValueError("unsupported command")
        return self._request(endpoint, "/command", {"command": command})
