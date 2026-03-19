#!/usr/bin/env python3
"""Visor web local y de solo lectura para la demo investigativa segura."""

from __future__ import annotations

import argparse
import html
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from init_demo_db import SCHEMA, seed_demo

TABLES = {
    "tenant": "SELECT id, name, country_code, created_at FROM tenant ORDER BY created_at DESC",
    "app_user": "SELECT username, full_name, email, is_active, created_at FROM app_user ORDER BY username",
    "case_file": "SELECT code, title, status, classification, opened_at FROM case_file ORDER BY opened_at DESC",
    "lead": "SELECT title, source_type, reliability_rating, confidence_rating, captured_at FROM lead ORDER BY captured_at DESC",
    "evidence": "SELECT title, evidence_type, storage_uri, sha256, created_at FROM evidence ORDER BY created_at DESC",
    "case_note": "SELECT note_type, body, created_at FROM case_note ORDER BY created_at DESC",
    "ai_model": "SELECT name, provider, endpoint, context_window, is_enabled FROM ai_model ORDER BY name",
    "ai_job": "SELECT job_type, status, prompt, response, created_at FROM ai_job ORDER BY created_at DESC",
}


def ensure_demo_db(db_path: Path, seed: bool) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        if seed:
            seed_demo(conn)


def query_rows(db_path: Path, query: str) -> tuple[list[str], list[tuple[object, ...]]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchall()
    if not rows:
        return [], []
    headers = list(rows[0].keys())
    data = [tuple(row) for row in rows]
    return headers, data


def render_table(headers: list[str], rows: list[tuple[object, ...]]) -> str:
    if not rows:
        return "<p>No hay registros.</p>"

    head_html = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    body_html = []
    for row in rows:
        cells = "".join(f"<td>{html.escape('' if value is None else str(value))}</td>" for value in row)
        body_html.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head_html}</tr></thead><tbody>{''.join(body_html)}</tbody></table>"


def render_home(db_path: Path) -> str:
    cards = []
    for name in TABLES:
        _, rows = query_rows(db_path, f"SELECT COUNT(*) AS total FROM {name}")
        total = rows[0][0] if rows else 0
        cards.append(
            f'<a class="card" href="/table?name={html.escape(name)}"><strong>{html.escape(name)}</strong><span>{total} registros</span></a>'
        )
    return f"""
    <h1>Plataforma investigativa segura</h1>
    <p>Visor local de solo lectura para inspeccionar la demo SQLite generada en <code>{html.escape(str(db_path))}</code>.</p>
    <div class="grid">{''.join(cards)}</div>
    <p class="hint">Este visor no ejecuta acciones de escritura; solo permite revisar datos de ejemplo.</p>
    """


def render_table_page(db_path: Path, table_name: str) -> str:
    query = TABLES.get(table_name)
    if not query:
        return "<h1>Tabla no encontrada</h1><p><a href='/'>Volver</a></p>"
    headers, rows = query_rows(db_path, query)
    return f"""
    <h1>Tabla: {html.escape(table_name)}</h1>
    <p><a href='/'>← Volver al inicio</a></p>
    {render_table(headers, rows)}
    """


def page_template(title: str, body: str) -> bytes:
    doc = f"""<!doctype html>
<html lang='es'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; background: #0f172a; color: #e2e8f0; }}
    a {{ color: #93c5fd; text-decoration: none; }}
    code {{ background: #1e293b; padding: 0.1rem 0.3rem; border-radius: 4px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-top: 1.5rem; }}
    .card {{ display: block; background: #111827; border: 1px solid #334155; border-radius: 10px; padding: 1rem; }}
    .card strong {{ display: block; margin-bottom: 0.5rem; }}
    .hint {{ color: #94a3b8; margin-top: 1rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; background: #111827; }}
    th, td {{ border: 1px solid #334155; padding: 0.65rem; text-align: left; vertical-align: top; }}
    th {{ background: #1e293b; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""
    return doc.encode("utf-8")


class DemoHandler(BaseHTTPRequestHandler):
    db_path: Path

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == "/":
            body = render_home(self.db_path)
            self.respond(200, page_template("Visor demo", body))
            return
        if parsed.path == "/table":
            table_name = params.get("name", [""])[0]
            body = render_table_page(self.db_path, table_name)
            status = 200 if table_name in TABLES else 404
            self.respond(status, page_template(f"Tabla {table_name}", body))
            return
        self.respond(404, page_template("No encontrado", "<h1>404</h1><p>Ruta no encontrada.</p>"))

    def log_message(self, format: str, *args: object) -> None:
        return

    def respond(self, status: int, payload: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Levanta un visor web local para la demo SQLite.")
    parser.add_argument("--db", type=Path, default=Path("intel_platform/demo.db"), help="Ruta del archivo SQLite")
    parser.add_argument("--host", default="127.0.0.1", help="Host de escucha")
    parser.add_argument("--port", type=int, default=8000, help="Puerto HTTP")
    parser.add_argument("--seed-if-missing", action="store_true", help="Crea y carga demo si la base no existe")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.seed_if_missing or not args.db.exists():
        ensure_demo_db(args.db, seed=True)

    if not args.db.exists():
        raise SystemExit(f"No existe la base demo: {args.db}. Ejecuta init_demo_db.py primero.")

    DemoHandler.db_path = args.db
    server = ThreadingHTTPServer((args.host, args.port), DemoHandler)
    print(f"Visor disponible en http://{args.host}:{args.port}")
    print(f"Base utilizada: {args.db}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
