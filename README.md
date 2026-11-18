# Mortgage Audit Engine

LLM/VLM-driven pipeline that audits complex banking processes (mortgage
origination and similar) from raw material — procedure documents, process-map
images, source code — and produces a structured **audit repository** plus a
formatted Word report with pain points, severity ratings, and agentic
AI / GenAI solution mappings.

## Layout

| Path | Purpose |
|---|---|
| `audit_tool/` | The audit engine: ingest → process model → pain-point audit → solution mapping → audit repository (SQLite + JSON). See `audit_tool/README.md`. |
| `charts.py` | Generates the report charts (process severity heatmap, findings by stage, priority matrix) from `audit_data.json`. |
| `create_report.js` | Builds the Word report from `audit_data.json` via docx-js. |
| `audit_data.json` | Baseline retail-mortgage dataset; also the mock fixture for offline runs. |
| `.env.example` | Endpoint configuration template (LLM + VLM). |

## Quick start

```bash
# offline dry-run (no model server needed)
python -m audit_tool run --mock --out ./audit_out
python -m audit_tool summary ./audit_out/audit_repo.sqlite

# real run against your model endpoints (see .env.example)
python -m audit_tool run \
    --procedure mortgage_procedure.pdf \
    --process-map process_map.png \
    --code-dir ./los-service \
    --out ./audit_out

# regenerate charts and the Word report from a fresh audit
cp audit_out/audit_data.json .
python3 charts.py
python3 /path/to/kimi-word/scripts/docx.py build create_report.js report.docx
```

## Principles

- **Evidence-gated** — every finding carries a verbatim source quote and a
  confidence level; low-confidence findings are flagged for human review.
- **Human-in-the-loop by design** — regulated credit decisions stay human
  (GDPR Art. 22, EU AI Act high-risk class); automation targets data
  movement, verification and documentation.
- **Living repository** — findings upsert by id, so re-running on updated
  inputs evolves the repo instead of replacing it.
