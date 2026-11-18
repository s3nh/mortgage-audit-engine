"""Persistence: the audit repository.

SQLite is the source of truth (queryable, diffable across runs); a JSON
export is written alongside for the report generator and for review.
Findings are keyed by id, so re-running the pipeline on updated inputs
upserts — the repo is a living artifact, not a one-shot dump.
"""
from __future__ import annotations

import json
import os
import sqlite3

from .schemas import AuditRepo, Finding, ProcessStage, Solution

DDL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at  TEXT NOT NULL,
    inputs      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stages (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    actors      TEXT,
    systems     TEXT,
    cycle_time  TEXT
);
CREATE TABLE IF NOT EXISTS findings (
    id          TEXT PRIMARY KEY,
    stage       TEXT NOT NULL REFERENCES stages(id),
    title       TEXT NOT NULL,
    category    TEXT NOT NULL,
    severity    TEXT NOT NULL,
    root_cause  TEXT,
    symptom     TEXT,
    evidence    TEXT,
    confidence  TEXT
);
CREATE TABLE IF NOT EXISTS solutions (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    addresses    TEXT NOT NULL,   -- JSON array of finding ids
    description  TEXT,
    hitl         TEXT,
    architecture TEXT,
    kpis         TEXT,
    impact       REAL,
    effort       REAL
);
"""


def save_repo(repo: AuditRepo, out_dir: str) -> dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    db_path = os.path.join(out_dir, "audit_repo.sqlite")
    json_path = os.path.join(out_dir, "audit_repo.json")

    with sqlite3.connect(db_path) as db:
        db.executescript(DDL)
        db.execute("INSERT INTO runs (created_at, inputs) VALUES (?, ?)",
                   (repo.meta.get("created_at", ""), json.dumps(repo.meta.get("inputs", {}))))
        for s in repo.stages:
            db.execute(
                "INSERT OR REPLACE INTO stages VALUES (?, ?, ?, ?, ?)",
                (s.id, s.name, s.actors, s.systems, s.cycle_time),
            )
        for f in repo.findings:
            db.execute(
                "INSERT OR REPLACE INTO findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (f.id, f.stage, f.title, f.category, f.severity,
                 f.root_cause, f.symptom, f.evidence, f.confidence),
            )
        for s in repo.solutions:
            db.execute(
                "INSERT OR REPLACE INTO solutions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (s.id, s.name, json.dumps(s.addresses), s.description,
                 s.hitl, s.architecture, s.kpis, s.impact, s.effort),
            )

    with open(json_path, "w", encoding="utf-8") as fh:
        fh.write(repo.to_json())
    return {"sqlite": db_path, "json": json_path}


def export_report_data(repo: AuditRepo, out_path: str) -> str:
    """Emit audit_data.json in the shape the docx report generator and the
    chart script already consume (stages/findings/solutions with the legacy
    field names)."""
    data = {
        "stages": [
            {"id": s.id, "name": s.name, "short": f"{s.id[1:]}. {s.name}",
             "actors": s.actors, "systems": s.systems, "cycle": s.cycle_time}
            for s in repo.stages
        ],
        "findings": [
            {"id": f.id, "stage": f.stage, "title": f.title,
             "category": f.category, "severity": f.severity,
             "root": f.root_cause, "symptom": f.symptom}
            for f in repo.findings
        ],
        "solutions": [
            {"id": s.id, "short": s.name.split("—")[0].strip()[:24], "name": s.name,
             "addresses": ", ".join(s.addresses), "desc": s.description,
             "hitl": s.hitl, "architecture": s.architecture, "kpis": s.kpis,
             "impact": s.impact, "effort": s.effort}
            for s in repo.solutions
        ],
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    return out_path
