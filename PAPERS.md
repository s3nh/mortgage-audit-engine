# Papers — Error Tracking & Failure Analysis in Agentic Flows

Curated reading list on error tracking, failure propagation, attribution and
observability in LLM agent systems, with relevance notes for this project.
Collected 2026-11-18 via Scholar; citation counts are directional, and 2026
items are mostly preprints.

## Failure taxonomies — how to classify agentic errors

| Paper | Venue / year | Why it matters here |
|---|---|---|
| [Characterizing Faults in Agentic AI: A Taxonomy of Types, Symptoms, and Root Causes](https://arxiv.org/abs/2603.06847) (Shah et al.) | arXiv 2026 | Taxonomy built to guide automated repair; directly reusable as a finding-classification scheme |
| [Demystifying the Lifecycle of Failures in Platform-Orchestrated Agentic Workflows](https://arxiv.org/abs/2509.23735) (Ma et al.) | arXiv 2025 | Agent-, workflow- and platform-level root causes; feeding the taxonomy into LLM prompts improves failure handling |
| [Failure Modes in LLM Systems: A System-Level Taxonomy for Reliable AI Applications](https://arxiv.org/abs/2511.19933) (Vinay) | arXiv 2025 | 15 failure modes across reasoning, tools and multi-agent workflows |
| [A Characterization Study of Bugs in LLM Agent Workflow Orchestration Frameworks](https://ieeexplore.ieee.org/abstract/document/11334467/) (Xue et al.) | IEEE/ACM ASE 2025 | Empirical: nine root-cause and six symptom categories from real framework bugs |
| [When Agents Fail to Act: A Diagnostic Framework for Tool Invocation Reliability in Multi-Agent LLM Systems](https://arxiv.org/abs/2601.16280) (Huang et al.) | arXiv 2026 | 12-category error taxonomy for tool-call failures |

## Error propagation & cascades — why one agent's error becomes everyone's

| Paper | Venue / year | Why it matters here |
|---|---|---|
| [Hallucination Cascade: Analyzing Error Propagation in Multi-Agent LLM Systems](https://arxiv.org/abs/2606.07937) (Jamshidi et al.) | arXiv 2026 | Models MAS as a sequential cascade where factual errors propagate and amplify |
| [From Spark to Fire: Modeling and Mitigating Error Cascades in LLM-Based Multi-Agent Collaboration](https://arxiv.org/abs/2603.04474) (Xie et al.) | arXiv 2026 | Error propagation forming false consensus as a system-level security risk |
| [Containing the Cascade: A Benchmark and Reference Mediator for Failure Propagation in Tool-Using LLM MAS](https://ieeexplore.ieee.org/abstract/document/11666599/) (Divi et al.) | IEEE 2026 | Argues we should measure containment, not just success |
| [On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents](https://arxiv.org/abs/2408.00989) (Huang et al.) | arXiv 2024 | Most-cited here (~154); topology choice (leader vs flat) determines how far errors spread |
| [PropUQ-MAS: Propagation-Aware Uncertainty Quantification for LLM Multi-Agent Systems](https://aclanthology.org/2026.emnlp-main.891/) (Liu et al.) | EMNLP 2026 | Tracks how uncertainty inherits and amplifies through intermediate messages |
| [Aegis: Automated Error Generation and Attribution for Multi-Agent Systems](https://proceedings.iclr.cc/paper_files/paper/2026/hash/56e8943ecd44b67bbea2702b9117b858-Abstract-Conference.html) (Kong et al.) | ICLR 2026 | Automated error generation + attribution for MAS failure analysis |
| [MAS-FIRE: Fault Injection and Reliability Evaluation for LLM-Based Multi-Agent Systems](https://arxiv.org/abs/2602.19843) (Jia et al.) | arXiv 2026 | Fault injection to measure silent fault propagation and cascading failures |

## Observability & tracing — the error-tracking infrastructure itself

| Paper | Venue / year | Why it matters here |
|---|---|---|
| [From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance in LLM Agents](https://arxiv.org/abs/2606.04990) (Wang et al.) | arXiv 2026 | The survey to read first: trace-based debugging and observability infrastructure |
| [AgentOps: Enabling Observability of LLM Agents](https://arxiv.org/abs/2411.05285) (Dong et al.) | arXiv 2024 | Span-based agent tracing; foundational for the tooling landscape (~120 citations) |
| [AgentTrace: A Structured Logging Framework for Agent System Observability](https://arxiv.org/abs/2602.10133) (AlSayyad et al.) | arXiv 2026 | Runtime instrumentation producing introspectable traces |
| [AgentDebugX: An Open-Source Toolkit for Failure Observability, Attribution, and Recovery in LLM Agents](https://arxiv.org/abs/2607.18754) (Zhu et al.) | arXiv 2026 | Traces symptoms backward to the agent and step whose correction fixes the run |
| [Seeing the Whole Elephant: A Benchmark for Failure Attribution in LLM-Based Multi-Agent Systems](https://aclanthology.org/2026.acl-long.912/) (Chen et al.) | ACL 2026 | Key design point: most traces capture only agent outputs, omitting the inputs and context needed for real debugging |
| [AgentSight: System-Level Observability for AI Agents Using eBPF](https://dl.acm.org/doi/abs/10.1145/3766882.3767169) (Zheng et al.) | ACM 2025 | Boundary tracing at OS level, when you cannot instrument the agent code itself |
| [A Survey for LLM Agent Trajectory Analysis: From Failure Attribution to Enhancement](https://arxiv.org/abs/2606.01581) (Wang et al.) | arXiv 2026 | Trajectory analysis from attribution through to agent improvement |
| [AgentFixer: From Failure Detection to Fix Recommendations in Agentic Systems](https://dl.acm.org/doi/abs/10.1145/3786167.3788427) (Mulian et al.) | ACM 2026 | Post-incident diagnosis producing fix recommendations |

## Design takeaways for `audit_tool`

1. **Store inputs + context, not just outputs** — failure attribution is
   impossible from output-only traces (Chen et al.). The audit repo already
   does this via `runs` + evidence quotes; keep it that way.
2. **Step-level traces beat one big log blob** — if run logging is added to
   the pipeline, record per-stage traces (stage input hash, prompt version,
   validation outcome), following AgentTrace / AgentDebugX.
3. **Classify before you fix** — adopt a failure taxonomy (Shah et al.,
   Ma et al.) for pipeline errors so recurring failure classes become visible
   in metrics, not just in ad-hoc debugging.

Raw search data: `papers_error_propagation.csv`, `papers_failure_analysis.csv`,
`papers_observability.csv` (kept locally in the workspace, not committed).
