"""
Hermes Agent HTTP 命令服务器
运行在 hermes-agent 容器内，接收 POST 请求执行 hermes CLI 并返回结果。
替代 docker.sock 方案，实现安全的网络隔离。
"""
import json
import logging
import os
import subprocess
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer

logging.basicConfig(level=logging.INFO, format="[CMD-SERVER] %(message)s")
logger = logging.getLogger("hermes-cmd-server")

HERMES_BIN = "/opt/hermes/.venv/bin/hermes"
LISTEN_PORT = int(os.environ.get("CMD_SERVER_PORT", "9888"))
ALLOWED_PREFIX = os.environ.get("CMD_SERVER_ALLOWED_PREFIX", "")
MAX_CONCURRENT = int(os.environ.get("CMD_SERVER_MAX_CONCURRENT", "3"))
_exec_semaphore = threading.Semaphore(MAX_CONCURRENT)

class Handler(BaseHTTPRequestHandler):
    """处理 POST /exec 请求"""

    # 静默日志
    def log_message(self, format, *args):
        pass

    def do_POST(self):
        if self.path != "/exec":
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0 or length > 1_000_000:  # 最大 1MB
                self.send_error(400, "Bad request body")
                return

            data = self.rfile.read(length)
            req = json.loads(data.decode("utf-8"))

            command = req.get("command", "").strip()
            timeout = min(int(req.get("timeout", 600)), 3600)  # 上限 1h
            env_vars = req.get("env", {})

            if not command:
                self._json_response({"success": False, "stdout": "", "stderr": "Empty command", "exit_code": -1}, 400)
                return

            # 可选的前缀白名单（安全性）
            if ALLOWED_PREFIX and not command.startswith(ALLOWED_PREFIX):
                self._json_response({"success": False, "stdout": "", "stderr": "Command not allowed", "exit_code": -1}, 403)
                return

            logger.info("exec: %s (timeout=%ds, waiting=%d)", command[:120], timeout,
                        MAX_CONCURRENT - _exec_semaphore._value)

            merged_env = {**os.environ, **env_vars}

            acquired = _exec_semaphore.acquire(timeout=5)
            if not acquired:
                self._json_response({"success": False, "stdout": "", "stderr": "Server busy (max concurrent: %d)" % MAX_CONCURRENT, "exit_code": -1}, 503)
                return

            try:
                result = subprocess.run(
                    ["bash", "-c", command],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=merged_env,
                )
                resp = {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                }
                logger.info("done: rc=%d out=%d err=%d", result.returncode, len(result.stdout), len(result.stderr))
                self._json_response(resp)

            except subprocess.TimeoutExpired:
                logger.warning("timeout: after %ds", timeout)
                self._json_response({"success": False, "stdout": "", "stderr": f"Timeout ({timeout}s)", "exit_code": -1})
            finally:
                _exec_semaphore.release()

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            logger.error("internal error: %s", e)
            self._json_response({"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}, 500)

    def _json_response(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    logger.info("starting on 0.0.0.0:%d", LISTEN_PORT)
    server = ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
