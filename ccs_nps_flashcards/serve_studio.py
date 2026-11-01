#!/usr/bin/env python3
"""Zero-404 Live Preview & Direct Download Hub Server for CCS (NPS) Rules 2021-2026 Flashcards.
Binds to 0.0.0.0:8080, permits any preview Host/Origin and iframe embedding, and serves:
  - / or /index.html -> ccs_nps_rules_interactive_studio.html (152 cards + instant downloads)
  - /download/<file>, /<file>, /ccs_nps_flashcards/<file> -> Content-Disposition: attachment
  - Any other GET route -> Studio app (zero 404 errors on preview subpaths)
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
from urllib.parse import unquote, urlparse

SERVE_DIR = Path(__file__).resolve().parent
STUDIO_FILE = SERVE_DIR / "ccs_nps_rules_interactive_studio.html"

DOWNLOADABLES = {
    "ccs_nps_rules_2021_flashcards_bundle.zip": "application/zip",
    "ccs_nps_rules_exam_flashcards.pdf": "application/pdf",
    "ccs_nps_rules_interactive_studio.html": "text/html; charset=utf-8",
    "ccs_nps_rules_exam_flashcards.md": "text/markdown; charset=utf-8",
    "ccs_nps_rules_anki_deck.tsv": "text/tab-separated-values; charset=utf-8",
    "ccs_nps_rules_flashcards.json": "application/json; charset=utf-8",
    "ccs_nps_rules_notebooklm_native.md": "text/markdown; charset=utf-8",
    "validation_report.md": "text/markdown; charset=utf-8",
    "README.md": "text/markdown; charset=utf-8",
}


class StudioHandler(BaseHTTPRequestHandler):
    def _send_common_headers(self, content_type: str, length: int, attachment_name: str | None = None) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        if attachment_name:
            self.send_header("Content-Disposition", f'attachment; filename="{attachment_name}"')
        self.end_headers()

    def _resolve_download(self, raw_path: str) -> tuple[Path, str, bool] | None:
        parsed = urlparse(raw_path)
        clean = unquote(parsed.path).strip("/")
        force_dl = "download" in parsed.query.lower() or clean.startswith("download/")
        if clean.startswith("download/"):
            clean = clean[len("download/") :]
        if clean.startswith("ccs_nps_flashcards/"):
            clean = clean[len("ccs_nps_flashcards/") :]

        if clean in DOWNLOADABLES:
            fpath = SERVE_DIR / clean
            if fpath.is_file():
                # Serving root HTML without ?download should render interactively unless /download/ was used
                if clean == "ccs_nps_rules_interactive_studio.html" and not force_dl:
                    return (fpath, DOWNLOADABLES[clean], False)
                return (fpath, DOWNLOADABLES[clean], True)
        return None

    def do_HEAD(self) -> None:  # noqa: N802
        dl = self._resolve_download(self.path)
        if dl:
            fpath, ctype, as_attach = dl
            self._send_common_headers(ctype, fpath.stat().st_size, fpath.name if as_attach else None)
            return
        data = STUDIO_FILE.read_bytes()
        self._send_common_headers("text/html; charset=utf-8", len(data))

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        dl = self._resolve_download(self.path)
        if dl:
            fpath, ctype, as_attach = dl
            data = fpath.read_bytes()
            self._send_common_headers(ctype, len(data), fpath.name if as_attach else None)
            self.wfile.write(data)
            return
        data = STUDIO_FILE.read_bytes()
        self._send_common_headers("text/html; charset=utf-8", len(data))
        self.wfile.write(data)


if __name__ == "__main__":
    mimetypes.init()
    server = ThreadingHTTPServer(("0.0.0.0", 8080), StudioHandler)
    print("Serving CCS (NPS) Rules 2021-2026 Interactive Studio & Download Hub on http://0.0.0.0:8080", flush=True)
    server.serve_forever()
