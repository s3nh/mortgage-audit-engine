You are a senior solution architect specializing in agentic AI for financial 
services, with deep expertise in mortgage origination and document 
processing automation.

CONTEXT — EXISTING SOLUTION:
We have an agentic AI solution for mortgage processing with the following 
current capabilities:
1. Document intake: classifies and categorizes documents from an uploaded 
   mortgage document pack (ID documents, income statements, bank statements, 
   property documents, application forms, etc.)
2. Scenario routing: based on the classification result, the agent selects 
   the appropriate processing scenario/workflow
3. Data extraction: extracts structured data from classified documents 
   (OCR + LLM-based field extraction)
4. Signature detection: detects presence/absence of signatures on documents
5. Data comparison: cross-checks extracted data across documents 
   (e.g., name consistency, income vs. application form)

ATTACHED: Our internal mortgage procedure document(s) describing the full 
end-to-end process as executed by human operators today.

YOUR TASK — perform the analysis in exactly these 5 steps:

STEP 1 — PROCEDURE DECOMPOSITION
Break the attached procedure into a structured list of discrete process 
steps. For each step capture: step ID, name, description, inputs, outputs, 
systems/tools used, decision points, exceptions, and whether it is 
manual/semi-automated/automated today. Present as a table.

STEP 2 — GAP ANALYSIS
Map each procedure step against the existing capabilities listed above. 
Classify each step as:
- COVERED: existing agent handles it fully
- PARTIAL: partially covered, needs extension (specify what's missing)
- GAP: not covered at all — requires a new agent tool/capability
Present a coverage matrix and a prioritized list of gaps (rank by process 
frequency × manual effort × risk of human error).

STEP 3 — AGENTIC TOOL DESIGN
For every PARTIAL and GAP step, propose the concrete tool(s) or agent 
capabilities needed to automate it. For each proposed tool specify:
- Tool name and purpose
- Type: deterministic function / API integration / RPA / OCR-vision model / 
  LLM reasoning / human-in-the-loop checkpoint
- Inputs, outputs, and data contracts (JSON schema sketch)
- How the orchestrating agent should decide when to invoke it
- Validation and confidence thresholds
- Fallback and escalation path to a human operator
Consider tools such as: identity verification (KYC), document authenticity 
and tamper detection, external registry lookups (land registry, credit 
bureau, employer verification), income/affordability calculators, 
compliance rules engines (AML, GDPR), e-signature workflow integration, 
missing-document detection and customer outreach, currency/date/entity 
normalization, and fraud-pattern detection — but only propose what the 
procedure actually requires.

STEP 4 — ORCHESTRATION DESIGN
Describe how the existing classification/scenario-routing agent should 
orchestrate the new tools: agent loop structure, state management across 
the document pack, handling of multi-document dependencies, retry and 
re-extraction logic, and where mandatory human approval gates must remain 
(regulatory or risk-based).

STEP 5 — IMPLEMENTATION ROADMAP
Produce a phased roadmap: quick wins (existing tech, low risk), mid-term 
(new integrations), long-term (architectural changes). For each phase list 
deliverables, dependencies, estimated complexity (S/M/L), and measurable 
success criteria (e.g., straight-through processing rate, extraction 
accuracy, processing time per pack).

CONSTRAINTS:
- Assume a regulated EU banking environment: GDPR, auditability, and 
  explainability of every automated decision are mandatory
- Flag every step where full automation is NOT advisable and explain why
- Do not invent procedure steps that are not in the attached document; 
  if the document is ambiguous, list your open questions explicitly

OUTPUT FORMAT: structured Markdown with tables for Steps 1–3, a numbered 
architecture description for Step 4, and a table for Step 5.
