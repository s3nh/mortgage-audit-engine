"""The audit pipeline: ingest -> process model -> pain points -> solutions.

Each stage validates strictly against the schema before the next stage runs,
so a malformed model response fails loudly at its own stage instead of
corrupting the repository.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from . import prompts
from .ingest import IngestBundle
from .schemas import AuditRepo, Finding, ProcessStage, Solution


def extract_process_model(llm, vlm, bundle: IngestBundle) -> list[ProcessStage]:
    """Stage 1: reconstruct the process model from docs (+ map via VLM)."""
    vision_note = ""
    messages = [{"role": "system", "content": prompts.SYSTEM}]
    if bundle.images:
        vision_note = (
            f"Additionally, {len(bundle.images)} process-map image(s) are "
            "attached. The visual flow is authoritative for stage sequence; "
            "reconcile it with the written procedure and note both."
        )
        prompt = prompts.PROCESS_MODEL.substitute(
            vision_note=vision_note, documents=bundle.document_block(),
        )
        for image in bundle.images:
            messages.append(vlm.image_message(prompt, image))
            prompt = "(same instructions; additional process-map image)"
    else:
        messages.append({
            "role": "user",
            "content": prompts.PROCESS_MODEL.substitute(
                vision_note=vision_note, documents=bundle.document_block(),
            ),
        })
    client = vlm if bundle.images else llm
    data = client.chat_json(messages)
    stages = [ProcessStage(**s) for s in data["stages"]]
    for s in stages:
        s.validate()
    return stages


def audit_pain_points(llm, bundle: IngestBundle, stages: list[ProcessStage]) -> list[Finding]:
    """Stage 2: the pain-point audit itself."""
    vision_section = ""
    if bundle.images:
        vision_section = (
            "Process-map image(s) were provided at stage 1; treat any mismatch "
            "between the documented flow and the mapped flow as a finding."
        )
    code_section = ""
    if bundle.code_snapshot:
        code_section = (
            "Code snapshot of implementing systems (look for hardcoded policy, "
            "manual-step markers, fragile point-to-point integration):\n"
            + bundle.code_snapshot
        )
    prompt = prompts.PAIN_POINTS.substitute(
        stages=json.dumps([s.__dict__ for s in stages], indent=1),
        documents=bundle.document_block(),
        vision_section=vision_section,
        code_section=code_section,
    )
    data = llm.chat_json([
        {"role": "system", "content": prompts.SYSTEM},
        {"role": "user", "content": prompt},
    ])
    findings = [Finding(**f) for f in data["findings"]]
    stage_ids = {s.id for s in stages}
    for f in findings:
        f.validate()
        if f.stage not in stage_ids:
            raise ValueError(f"{f.id}: unknown stage {f.stage!r}")
    return findings


def map_solutions(llm, findings: list[Finding]) -> list[Solution]:
    """Stage 3: cluster findings into agentic-AI solution blocks."""
    prompt = prompts.SOLUTIONS.substitute(
        findings=json.dumps([f.__dict__ for f in findings], indent=1),
    )
    data = llm.chat_json([
        {"role": "system", "content": prompts.SYSTEM},
        {"role": "user", "content": prompt},
    ])
    solutions = [Solution(**s) for s in data["solutions"]]
    known = {f.id for f in findings}
    for s in solutions:
        s.validate(known)
    covered = {f for s in solutions for f in s.addresses}
    uncovered = [f.id for f in findings
                 if f.severity in ("Critical", "High") and f.id not in covered]
    if uncovered:
        raise ValueError(f"solutions leave Critical/High findings unaddressed: {uncovered}")
    return solutions


def run_pipeline(llm, vlm, bundle: IngestBundle) -> AuditRepo:
    stages = extract_process_model(llm, vlm, bundle)
    findings = audit_pain_points(llm, bundle, stages)
    solutions = map_solutions(llm, findings)
    repo = AuditRepo(
        stages=stages,
        findings=findings,
        solutions=solutions,
        meta={
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "inputs": {
                "documents": [src for src, _ in bundle.documents],
                "process_maps": bundle.images,
                "code_snapshot": bool(bundle.code_snapshot),
            },
        },
    )
    repo.validate()
    return repo
