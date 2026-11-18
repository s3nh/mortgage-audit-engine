"""Command line interface.

  # full run against a vLLM server (env vars point at the endpoints)
  python -m audit_tool run \
      --procedure procedure.pdf --process-map map.png \
      --code-dir ./los-service --out ./audit_out

  # offline dry-run with the bundled baseline fixture (no model needed)
  python -m audit_tool run --mock --out ./audit_out

  # inspect the repo
  python -m audit_tool summary ./audit_out/audit_repo.sqlite
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys

from .config import AuditConfig
from .ingest import build_bundle
from .llm import MockClient, OpenAICompatClient
from .pipeline import run_pipeline
from .schemas import AuditRepo
from .store import export_report_data, save_repo

FIXTURE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "audit_data.json")


def _legacy_fixture_to_repo(path: str) -> AuditRepo:
    """Adapt the existing baseline audit_data.json into an AuditRepo."""
    import json
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    return AuditRepo.from_dict({
        "meta": {"source": "baseline fixture"},
        "stages": [{"id": s["id"], "name": s["name"], "actors": s["actors"],
                    "systems": s["systems"], "cycle_time": s["cycle"]}
                   for s in d["stages"]],
        "findings": [{"id": f["id"], "stage": f["stage"], "title": f["title"],
                      "category": f["category"], "severity": f["severity"],
                      "root_cause": f["root"], "symptom": f["symptom"],
                      "evidence": "(baseline finding, pre-recalibration)",
                      "confidence": "medium"}
                     for f in d["findings"]],
        "solutions": [{"id": s["id"], "name": s["name"],
                       "addresses": [x.strip() for x in s["addresses"].split(",")],
                       "description": s["desc"], "hitl": s["hitl"],
                       "architecture": s["architecture"], "kpis": s["kpis"],
                       "impact": s["impact"], "effort": s["effort"]}
                      for s in d["solutions"]],
    })


def cmd_run(args: argparse.Namespace) -> int:
    cfg = AuditConfig.from_env()
    bundle = build_bundle(
        procedures=args.procedure or [],
        process_maps=args.process_map or [],
        code_dir=args.code_dir,
        max_code_files=cfg.max_code_files,
    )
    if args.mock:
        repo = _legacy_fixture_to_repo(args.fixture or FIXTURE)
        llm = vlm = MockClient(repo)
        print(f"[mock] replaying fixture: {args.fixture or FIXTURE}")
    else:
        llm = OpenAICompatClient(cfg.llm, cfg.temperature, cfg.request_timeout_s)
        vlm = OpenAICompatClient(cfg.vlm, cfg.temperature, cfg.request_timeout_s)
        print(f"LLM: {cfg.llm.base_url} ({cfg.llm.model})")
        if bundle.images:
            print(f"VLM: {cfg.vlm.base_url} ({cfg.vlm.model})")

    repo = run_pipeline(llm, vlm, bundle)
    paths = save_repo(repo, args.out)
    report_data = export_report_data(repo, os.path.join(args.out, "audit_data.json"))

    crit = sum(1 for f in repo.findings if f.severity == "Critical")
    high = sum(1 for f in repo.findings if f.severity == "High")
    print(f"\nAudit complete: {len(repo.stages)} stages, {len(repo.findings)} findings "
          f"({crit} Critical / {high} High), {len(repo.solutions)} solution blocks")
    print(f"  sqlite : {paths['sqlite']}")
    print(f"  json   : {paths['json']}")
    print(f"  report : {report_data}  (feed to charts.py / create_report.js)")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    with sqlite3.connect(args.db) as db:
        print("Findings by severity:")
        for sev, n in db.execute(
                "SELECT severity, COUNT(*) FROM findings GROUP BY severity "
                "ORDER BY CASE severity WHEN 'Critical' THEN 0 WHEN 'High' THEN 1 "
                "WHEN 'Medium' THEN 2 ELSE 3 END"):
            print(f"  {sev:<9} {n}")
        print("\nLow-confidence findings (need human review):")
        for fid, title in db.execute(
                "SELECT id, title FROM findings WHERE confidence = 'low'"):
            print(f"  {fid}  {title}")
        print("\nSolutions:")
        for sid, name, impact, effort in db.execute(
                "SELECT id, name, impact, effort FROM solutions ORDER BY id"):
            print(f"  {sid}. {name}  (impact {impact}, effort {effort})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="audit_tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run the audit pipeline")
    run.add_argument("--procedure", action="append",
                     help="procedure document (pdf/docx/txt/md); repeatable")
    run.add_argument("--process-map", action="append",
                     help="process map image (png/jpg/...); analysed by the VLM")
    run.add_argument("--code-dir", help="source tree of implementing systems")
    run.add_argument("--out", default="./audit_out", help="output directory")
    run.add_argument("--mock", action="store_true",
                     help="offline dry-run with a fixture repo (no model calls)")
    run.add_argument("--fixture", help="custom mock fixture (legacy audit_data.json)")
    run.set_defaults(func=cmd_run)

    summ = sub.add_parser("summary", help="summarise an audit repository")
    summ.add_argument("db", help="path to audit_repo.sqlite")
    summ.set_defaults(func=cmd_summary)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
