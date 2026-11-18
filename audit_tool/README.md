# Mortgage Process Audit Engine

LLM/VLM-driven pipeline that turns raw process material (procedure documents,
process-map images, source code) into a structured **audit repository**, and
from there into the audit report.

## How it works

```
procedure docs (pdf/docx/txt/md) ─┐
process map images (png/jpg) ─────┤   stage 1: process model (LLM, or VLM when
source code tree (optional) ──────┘   images are present — the map is treated
                                      as authoritative for flow sequence)
                                            │
                                      stage 2: pain-point audit (LLM)
                                      7 categories, severity scoring,
                                      verbatim evidence quotes per finding
                                            │
                                      stage 3: solution mapping (LLM)
                                      findings clustered into agentic-AI
                                      blocks, HITL boundaries, impact/effort
                                            │
                                            ▼
                              audit_repo.sqlite  (source of truth)
                              audit_repo.json    (review/diff)
                              audit_data.json    (feeds charts.py +
                                                  create_report.js → .docx)
```

Every stage validates strictly against the schema (`schemas.py`); malformed
model output triggers one self-repair retry and then fails loudly — nothing
is silently patched.

## Setup

No third-party runtime dependencies for the core engine (standard library
only). Document loaders use `pypdf` / `python-docx` when you feed PDF or
Word files.

Point the engine at your model endpoints (any OpenAI-compatible server —
vLLM, LiteLLM, internal gateway, hosted API):

```bash
export AUDIT_LLM_BASE_URL=http://localhost:8000/v1
export AUDIT_LLM_MODEL=Qwen/Qwen2.5-72B-Instruct
export AUDIT_LLM_API_KEY=...           # if required
export AUDIT_VLM_BASE_URL=http://localhost:8001/v1   # vision model
export AUDIT_VLM_MODEL=Qwen/Qwen2.5-VL-72B-Instruct
```

## Usage

```bash
# offline dry-run (no model server needed) — replays the baseline fixture
python -m audit_tool run --mock --out ./audit_out

# real run
python -m audit_tool run \
    --procedure mortgage_procedure.pdf \
    --process-map process_map.png \
    --code-dir ./los-service \
    --out ./audit_out

# inspect the repository
python -m audit_tool summary ./audit_out/audit_repo.sqlite

# regenerate the report from the repo
python3 charts.py                                        # charts from audit_data.json
python3 docx.py build create_report.js report.docx       # Word report
```

## Design decisions

- **Evidence-gated findings** — every finding carries a verbatim `evidence`
  quote from the source material and a `confidence` level. Low-confidence
  findings are flagged for human review (`summary` lists them), not hidden.
- **HITL by design** — the solution prompt hard-codes the constraint that
  regulated credit decisions stay human (GDPR Art. 22, EU AI Act high-risk
  class); solutions automate data movement, verification and documentation.
- **Living repository** — findings upsert by id, so re-running the pipeline
  on updated inputs evolves the repo instead of replacing it; the `runs`
  table keeps the history of inputs per run.
- **Mock mode** — the full pipeline (ingest → prompts → validation → store
  → export) runs without a GPU for development and CI.
