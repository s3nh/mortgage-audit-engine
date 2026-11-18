"""Data model of the audit repository.

Deliberately dependency-free (dataclasses, not pydantic) so the engine runs
on a bare Python install. Validation is explicit and strict: anything the
LLM returns that does not conform is rejected and re-asked, never silently
patched.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

SEVERITIES = ("Critical", "High", "Medium", "Low")
CATEGORIES = (
    "Manual work / re-entry",
    "Process design",
    "Integration fragility",
    "Compliance / risk",
    "Redundancy",
    "Agility",
    "Customer experience",
)


class ValidationError(ValueError):
    pass


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValidationError(msg)


@dataclass
class ProcessStage:
    id: str                 # S1..Sn
    name: str
    actors: str
    systems: str
    cycle_time: str

    def validate(self) -> None:
        _require(bool(self.id and self.name), f"stage missing id/name: {self!r}")


@dataclass
class Finding:
    id: str                 # PP-01..
    stage: str              # stage id reference
    title: str
    category: str
    severity: str
    root_cause: str
    symptom: str
    evidence: str = ""      # verbatim quote from the source material
    confidence: str = "medium"   # high | medium | low — needs human review when low

    def validate(self) -> None:
        _require(self.severity in SEVERITIES, f"{self.id}: bad severity {self.severity!r}")
        _require(self.category in CATEGORIES, f"{self.id}: bad category {self.category!r}")
        _require(bool(self.title and self.root_cause), f"{self.id}: missing title/root_cause")
        _require(self.confidence in ("high", "medium", "low"), f"{self.id}: bad confidence")


@dataclass
class Solution:
    id: str                 # A..H
    name: str
    addresses: list[str]    # finding ids
    description: str
    hitl: str               # human-in-the-loop boundary
    architecture: str
    kpis: str
    impact: float           # 1..10
    effort: float           # 1..10

    def validate(self, known_finding_ids: set[str]) -> None:
        _require(bool(self.id and self.name and self.description), f"solution incomplete: {self!r}")
        _require(1 <= self.impact <= 10 and 1 <= self.effort <= 10,
                 f"{self.id}: impact/effort out of range")
        unknown = [f for f in self.addresses if f not in known_finding_ids]
        _require(not unknown, f"{self.id}: references unknown findings {unknown}")


@dataclass
class AuditRepo:
    stages: list[ProcessStage] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    solutions: list[Solution] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        stage_ids = {s.id for s in self.stages}
        for s in self.stages:
            s.validate()
        for f in self.findings:
            f.validate()
            _require(f.stage in stage_ids, f"{f.id}: unknown stage {f.stage!r}")
        finding_ids = {f.id for f in self.findings}
        _require(len(finding_ids) == len(self.findings), "duplicate finding ids")
        for s in self.solutions:
            s.validate(finding_ids)

    # ---- (de)serialisation ----------
    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": self.meta,
            "stages": [asdict(s) for s in self.stages],
            "findings": [asdict(f) for f in self.findings],
            "solutions": [asdict(s) for s in self.solutions],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "AuditRepo":
        repo = AuditRepo(
            stages=[ProcessStage(**s) for s in d.get("stages", [])],
            findings=[Finding(**f) for f in d.get("findings", [])],
            solutions=[Solution(**s) for s in d.get("solutions", [])],
            meta=d.get("meta", {}),
        )
        repo.validate()
        return repo

    @staticmethod
    def from_json(text: str) -> "AuditRepo":
        return AuditRepo.from_dict(json.loads(text))
