"""Prompt templates. Kept as plain functions (string.Template) so they are
easy to review, diff and tune — prompts are the audit methodology, treat
them as code.
"""
from __future__ import annotations

from string import Template

SYSTEM = (
    "You are a senior banking operations auditor specialising in retail "
    "lending processes and applied AI. You write precise, evidence-based "
    "findings. You never invent facts: every finding must be traceable to "
    "the supplied material, and uncertainty is stated as low confidence "
    "rather than hidden. You reply with JSON only."
)

PROCESS_MODEL = Template("""PROCESS MODEL EXTRACTION

Reconstruct the end-to-end process model from the material below.

$vision_note

MATERIAL:
$documents

Return ONLY a JSON object:
{
  "stages": [
    {"id": "S1", "name": "...", "actors": "...", "systems": "...", "cycle_time": "..."}
  ]
}

Rules:
- 5 to 12 stages, ordered as the process actually flows.
- id values are S1, S2, ... in order.
- cycle_time: use the material if stated, otherwise "unknown".
- systems: the systems named in the material; "not specified" if absent.
""")

PAIN_POINTS = Template("""PAIN-POINT AUDIT

Process model:
$stages

Source material:
$documents

$vision_section

$code_section

Audit every stage for pain points in these categories:
Manual work / re-entry | Process design | Integration fragility |
Compliance / risk | Redundancy | Agility | Customer experience

For EACH stage, check specifically: manual data re-keying between systems,
missing exception/rejection paths, swivel-chair handoffs, duplicated checks,
single points of knowledge, weak audit trails, exception handling escaping
into email, and disagreements between the written procedure and the process
map (treat each disagreement as a finding — it marks undocumented reality).

Return ONLY a JSON object:
{
  "findings": [
    {
      "id": "PP-01", "stage": "S1", "title": "...",
      "category": "one of the categories above, exactly",
      "severity": "Critical | High | Medium | Low",
      "root_cause": "...", "symptom": "...",
      "evidence": "verbatim quote from the source material",
      "confidence": "high | medium | low"
    }
  ]
}

Rules:
- Severity: Critical = direct financial/regulatory harm or process blockage;
  High = significant recurring cost/delay/risk; Medium = friction; Low = minor.
- evidence must be a verbatim quote; if the source material does not support
  the finding, set confidence to "low" and say what is missing in evidence.
- Do not pad. Only real, defensible findings.
""")

SOLUTIONS = Template("""SOLUTION MAPPING

Findings:
$findings

For the findings above, design agentic AI / GenAI solution blocks. Cluster
findings so one shared capability removes several findings at once.

Return ONLY a JSON object:
{
  "solutions": [
    {
      "id": "A", "name": "...",
      "addresses": ["PP-01", "PP-04"],
      "description": "what the agent does, concretely",
      "hitl": "exactly where a human stays in the loop and why",
      "architecture": "one-paragraph architecture sketch",
      "kpis": "comma-separated KPI names",
      "impact": 8.5, "effort": 4.0
    }
  ]
}

Rules:
- Every Critical and High finding must be addressed by at least one solution.
- impact and effort are 1-10 floats.
- Regulated credit decisions stay human-in-the-loop by design (GDPR Art. 22,
  EU AI Act high-risk class). Do not propose fully automated credit approval.
- Prefer augmentation over automation where judgement or accountability is
  central; automate data movement, verification and documentation.
""")
