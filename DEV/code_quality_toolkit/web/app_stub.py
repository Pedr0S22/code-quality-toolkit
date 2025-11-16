"""Minimal HTTP server that serves report.json content."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Tuple

REPORT_FILE = Path("report.json")


class ReportHandler(BaseHTTPRequestHandler):
    server_version = "ToolkitStub/0.1"

    def do_GET(self) -> None:  # noqa: N802 - HTTP verb required
        if self.path == "/api/report":
            self._serve_json(self._load_report())
        elif self.path == "/api/summary":
            report = self._load_report()
            if report is None:
                self._respond_not_found()
            else:
                summary = report.get("summary", {})
                self._serve_json(summary)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def _serve_json(self, payload: dict | None) -> None:
        if payload is None:
            self._respond_not_found()
            return
        data = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _load_report(self) -> dict | None:
        if not REPORT_FILE.exists():
            return None
        return json.loads(REPORT_FILE.read_text(encoding="utf-8"))

    def _respond_not_found(self) -> None:
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"report.json not found. Execute a analise pela CLI primeiro.")


# EXTENSION-POINT: substituir por framework completo (FastAPI/Starlette) conforme necessário.

def run_server(address: Tuple[str, int] = ("127.0.0.1", 8000)) -> None:
    """Run the development HTTP server."""

    httpd = HTTPServer(address, ReportHandler)
    print(f"Serving report API on http://{address[0]}:{address[1]}")
    httpd.serve_forever()


if __name__ == "__main__":  # pragma: no cover
    run_server()
