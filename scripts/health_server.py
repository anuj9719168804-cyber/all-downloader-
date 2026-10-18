"""
Minimal HTTP health endpoint so hosts that require an open port (e.g. Render
Web Services) see the service as alive.

Responds with "ok" to every GET/HEAD request. It serves no files and exposes
no project data. Listens on $PORT (default 8080).
"""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def _reply(self):
        body = b"ok"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    do_GET = _reply
    do_HEAD = _reply

    def log_message(self, format, *args):
        # keep Render logs clean
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"health server listening on :{port}", flush=True)
    server.serve_forever()
