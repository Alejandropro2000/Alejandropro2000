#!/usr/bin/env python3
"""Inicializa una demo local en SQLite para la plataforma investigativa segura."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tenant (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country_code TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_user (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    username TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, username),
    FOREIGN KEY (tenant_id) REFERENCES tenant(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS case_file (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    code TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    status TEXT NOT NULL,
    classification TEXT NOT NULL,
    opened_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT NOT NULL,
    UNIQUE (tenant_id, code),
    FOREIGN KEY (tenant_id) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES app_user(id)
);

CREATE TABLE IF NOT EXISTS lead (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    case_id TEXT,
    source_type TEXT NOT NULL,
    reliability_rating INTEGER NOT NULL,
    confidence_rating INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (case_id) REFERENCES case_file(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES app_user(id)
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    title TEXT NOT NULL,
    storage_uri TEXT NOT NULL,
    sha256 TEXT,
    chain_of_custody TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (case_id) REFERENCES case_file(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES app_user(id)
);

CREATE TABLE IF NOT EXISTS case_note (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    body TEXT NOT NULL,
    note_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES case_file(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES app_user(id)
);

CREATE TABLE IF NOT EXISTS ai_model (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    context_window INTEGER,
    is_enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenant(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_job (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    case_id TEXT,
    requested_by TEXT NOT NULL,
    model_id TEXT NOT NULL,
    job_type TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenant(id) ON DELETE CASCADE,
    FOREIGN KEY (case_id) REFERENCES case_file(id) ON DELETE SET NULL,
    FOREIGN KEY (requested_by) REFERENCES app_user(id),
    FOREIGN KEY (model_id) REFERENCES ai_model(id)
);
"""

SEED = {
    "tenant": ("tenant-demo", "Unidad Analítica Demo", "PY"),
    "users": [
        ("user-ana", "tenant-demo", "ana", "Ana Rojas", "ana@example.local", "demo-hash"),
        ("user-luis", "tenant-demo", "luis", "Luis Vera", "luis@example.local", "demo-hash"),
    ],
    "case": (
        "case-001",
        "tenant-demo",
        "EXP-2026-001",
        "Caso demostrativo de fraude documental",
        "Expediente de ejemplo para validar flujos de análisis, evidencia y notas.",
        "open",
        "confidential",
        "user-ana",
    ),
    "lead": (
        "lead-001",
        "tenant-demo",
        "case-001",
        "open_source",
        4,
        3,
        "Publicación vinculada al caso",
        "Registro de ejemplo para demostrar trazabilidad y análisis humano supervisado.",
        "user-ana",
    ),
    "evidence": (
        "ev-001",
        "tenant-demo",
        "case-001",
        "document",
        "Informe preliminar",
        "s3://demo-bucket/informes/preliminar.pdf",
        "abc123demo",
        json.dumps([{"step": 1, "action": "ingreso", "by": "Ana Rojas"}], ensure_ascii=False),
        "user-luis",
    ),
    "note": (
        "note-001",
        "case-001",
        "user-ana",
        "La IA puede resumir documentos, pero la valoración probatoria debe ser humana.",
        "analysis",
    ),
    "model": (
        "model-001",
        "tenant-demo",
        "llama3.1:8b-instruct",
        "ollama",
        "http://localhost:11434",
        8192,
    ),
    "job": (
        "job-001",
        "tenant-demo",
        "case-001",
        "user-ana",
        "model-001",
        "summarization",
        "Resume el expediente con foco en hechos confirmados.",
        "Borrador generado para revisión humana.",
        "completed",
    ),
}


def seed_demo(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT OR IGNORE INTO tenant (id, name, country_code) VALUES (?, ?, ?)", SEED["tenant"])
    conn.executemany(
        "INSERT OR IGNORE INTO app_user (id, tenant_id, username, full_name, email, password_hash) VALUES (?, ?, ?, ?, ?, ?)",
        SEED["users"],
    )
    conn.execute(
        "INSERT OR IGNORE INTO case_file (id, tenant_id, code, title, summary, status, classification, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        SEED["case"],
    )
    conn.execute(
        "INSERT OR IGNORE INTO lead (id, tenant_id, case_id, source_type, reliability_rating, confidence_rating, title, content, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        SEED["lead"],
    )
    conn.execute(
        "INSERT OR IGNORE INTO evidence (id, tenant_id, case_id, evidence_type, title, storage_uri, sha256, chain_of_custody, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        SEED["evidence"],
    )
    conn.execute(
        "INSERT OR IGNORE INTO case_note (id, case_id, author_id, body, note_type) VALUES (?, ?, ?, ?, ?)",
        SEED["note"],
    )
    conn.execute(
        "INSERT OR IGNORE INTO ai_model (id, tenant_id, name, provider, endpoint, context_window) VALUES (?, ?, ?, ?, ?, ?)",
        SEED["model"],
    )
    conn.execute(
        "INSERT OR IGNORE INTO ai_job (id, tenant_id, case_id, requested_by, model_id, job_type, prompt, response, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        SEED["job"],
    )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Inicializa una demo SQLite de la plataforma investigativa segura.")
    parser.add_argument("--db", type=Path, default=Path("intel_platform/demo.db"), help="Ruta del archivo SQLite")
    parser.add_argument("--seed", action="store_true", help="Carga datos de demostración")
    args = parser.parse_args()

    args.db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.db) as conn:
        conn.executescript(SCHEMA)
        if args.seed:
            seed_demo(conn)

        totals = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("tenant", "app_user", "case_file", "lead", "evidence", "case_note", "ai_model", "ai_job")
        }

    print(f"Base demo inicializada en: {args.db}")
    for table, count in totals.items():
        print(f"- {table}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
