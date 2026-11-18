import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType,
  BorderStyle,
  Document,
  Footer,
  Header,
  HeadingLevel,
  ImageRun,
  ImportedXmlComponent,
  LevelFormat,
  Packer,
  PageBreak,
  PageNumber,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
  convertInchesToTwip,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node create_report.js /abs/out.docx");
const outputDir = path.dirname(outputPath);
const assetDir = path.join(outputDir, "assets");
const DATA = JSON.parse(
  fs.readFileSync(path.join(outputDir, "audit_data.json"), "utf-8"),
);

const T = String.raw;
const palette = {
  dark: "263238",
  primary: "37474F",
  light: "78909C",
  border: "D8E0E3",
  fill: "EEF3F6",
  teal: "2E6E63",
  critical: "8E3B2F",
  high: "C07A3E",
  medium: "9C8A3C",
};
const sevColor = (s) =>
  s === "Critical" ? palette.critical : s === "High" ? palette.high : palette.medium;

const font = {
  ascii: "Times New Roman",
  hAnsi: "Times New Roman",
  cs: "Times New Roman",
  eastAsia: "SimSun",
};

const run = (text, options = {}) =>
  new TextRun({ text, font, size: 22, ...options });

const para = (children, options = {}) =>
  new Paragraph({
    spacing: { after: 140, line: 290 },
    ...options,
    children: Array.isArray(children) ? children : [children],
  });

const body = (text, options = {}) =>
  para(run(text), {
    indent: { firstLine: convertInchesToTwip(0.3) },
    ...options,
  });

const bullet = (text) =>
  para(run(text), {
    numbering: { reference: "bullets", level: 0 },
    indent: undefined,
  });

const h1 = (text) =>
  para(run(text, { bold: true, size: 30, color: palette.dark }), {
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 160 },
  });
const h2 = (text) =>
  para(run(text, { bold: true, size: 25, color: palette.primary }), {
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120 },
  });
const h3 = (text) =>
  para(run(text, { bold: true, size: 22, color: palette.teal }), {
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 100 },
  });

const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

const cell = (children, options = {}) =>
  new TableCell({
    children: Array.isArray(children) ? children : [children],
    margins: { top: 90, bottom: 90, left: 110, right: 110 },
    ...options,
  });
const cellP = (text, options = {}) =>
  para(run(text, options), { spacing: { after: 0, line: 260 } });

const caption = (text) =>
  para(run(text, { italics: true, size: 19, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 200 },
  });

const img = (file, w, h) =>
  para(
    new ImageRun({
      type: "png",
      data: fs.readFileSync(path.join(assetDir, file)),
      transformation: { width: w, height: h },
    }),
    { alignment: AlignmentType.CENTER, spacing: { after: 0 } },
  );

const xmlEscape = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

const toc = (entries) => {
  const cached = entries
    .map(({ title, level, page }) => {
      const indent = Math.max(0, level - 1) * 360;
      return `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/>
        <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs>
        <w:ind w:left="${indent}"/></w:pPr>
        <w:r><w:t>${xmlEscape(title)}</w:t></w:r>
        <w:r><w:tab/></w:r>
        <w:r><w:t>${page}</w:t></w:r></w:p>`;
    })
    .join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:sdtPr><w:alias w:val="Table of Contents"/></w:sdtPr>
    <w:sdtContent>
      <w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>
        <w:instrText xml:space="preserve"> TOC \\o &quot;1-3&quot; \\h \\z \\u </w:instrText>
        <w:fldChar w:fldCharType="separate"/></w:r></w:p>
      ${cached}
      <w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
    </w:sdtContent>
  </w:sdt>`).root[0];
};

// ---------- shared tables ----------
const TEXT_W = 9026; // A4 width minus 1" margins, DXA

const stageTable = () => {
  const widths = [2050, 2000, 2800, 2176];
  const header = ["Stage", "Key actors", "Systems typically involved", "Typical cycle time"].map(
    (t, i) =>
      cell(cellP(t, { bold: true }), {
        width: { size: widths[i], type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: palette.fill },
      }),
  );
  const rows = DATA.stages.map(
    (s) =>
      new TableRow({
        children: [
          cell(cellP(s.name, { bold: true }), {
            width: { size: widths[0], type: WidthType.DXA },
          }),
          cell(cellP(s.actors), { width: { size: widths[1], type: WidthType.DXA } }),
          cell(cellP(s.systems), { width: { size: widths[2], type: WidthType.DXA } }),
          cell(cellP(s.cycle), { width: { size: widths[3], type: WidthType.DXA } }),
        ],
      }),
  );
  return new Table({
    width: { size: TEXT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [new TableRow({ children: header, tableHeader: true }), ...rows],
  });
};

const findingsSummaryTable = () => {
  const widths = [800, 800, 4400, 1800, 1226];
  const header = ["ID", "Stage", "Finding", "Category", "Severity"].map((t, i) =>
    cell(cellP(t, { bold: true }), {
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: palette.fill },
    }),
  );
  const rows = DATA.findings.map(
    (f) =>
      new TableRow({
        children: [
          cell(cellP(f.id, { bold: true }), { width: { size: widths[0], type: WidthType.DXA } }),
          cell(cellP(f.stage), { width: { size: widths[1], type: WidthType.DXA } }),
          cell(cellP(f.title, { size: 20 }), { width: { size: widths[2], type: WidthType.DXA } }),
          cell(cellP(f.category, { size: 20 }), { width: { size: widths[3], type: WidthType.DXA } }),
          cell(cellP(f.severity, { bold: true, color: sevColor(f.severity) }), {
            width: { size: widths[4], type: WidthType.DXA },
          }),
        ],
      }),
  );
  return new Table({
    width: { size: TEXT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [new TableRow({ children: header, tableHeader: true }), ...rows],
  });
};

const kpiTable = () => {
  const widths = [2900, 2800, 3326];
  const header = ["KPI", "Typical baseline (today)", "Directional target (post-implementation)"].map(
    (t, i) =>
      cell(cellP(t, { bold: true }), {
        width: { size: widths[i], type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: palette.fill },
      }),
  );
  const rows = [
    ["Time-to-decision (application to credit decision)", "10–20 working days", "3–7 working days"],
    ["Document collection cycle time", "3–10 days, untracked", "Same day – 2 days, fully tracked"],
    ["Rework loops per file (incomplete submissions)", "2–4 round trips", "Under 1 round trip"],
    ["Manual data entry per file", "60–120 minutes", "Under 15 minutes"],
    ["Straight-through processing (simple cases)", "0–10%", "30–50%"],
    ["Document fraud detection point", "Post-disbursement or never", "Pre-decision, 100% of files screened"],
    ["Underwriter time on file assembly vs. decision", "Majority on assembly", "Majority on judgement"],
    ["Approval-to-disbursement conversion", "Leakage unmeasured", "Leakage measured and actively managed"],
    ["Customer status calls to contact centre", "Baseline volume", "−40–60% via proactive updates"],
    ["Audit evidence retrieval time", "Days of manual search", "Minutes, from structured evidence store"],
  ].map(
    (r) =>
      new TableRow({
        children: r.map((t, i) =>
          cell(cellP(t, i === 0 ? { bold: true } : {}), {
            width: { size: widths[i], type: WidthType.DXA },
          }),
        ),
      }),
  );
  return new Table({
    width: { size: TEXT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [new TableRow({ children: header, tableHeader: true }), ...rows],
  });
};

const roadmapTable = () => {
  const widths = [1300, 2200, 3326, 2200];
  const header = ["Phase", "Timeline", "Scope", "Exit criteria"].map((t, i) =>
    cell(cellP(t, { bold: true }), {
      width: { size: widths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: palette.fill },
    }),
  );
  const rows = [
    ["0 — Foundations", "Months 0–2",
     "Canonical application data model; API access to LOS/DMS; document store hygiene; agent governance and model-risk guardrails approved by risk and compliance.",
     "Data model signed off; guardrail framework approved; pilot scope agreed."],
    ["1 — Quick wins", "Months 2–6",
     "Solution A (document intelligence) pilot on live files; Solution G (offer generation + disbursement checklist); Solution B (smart intake) on one channel.",
     "Extraction accuracy above agreed threshold; measurable drop in document cycle time; offer defects near zero."],
    ["2 — Core credit", "Months 6–12",
     "Solution D (income & affordability verification, policy-as-code); Solution F (underwriting copilot) pilot with strict human-in-the-loop.",
     "Underwriter time per file reduced; rationale quality sampled and passing; regulator/compliance comfortable with oversight model."],
    ["3 — Scale & close the loop", "Months 12–18",
     "Solution C (perpetual KYC), Solution E (valuation orchestration + AVM cross-check), Solution H (servicing handover & monitoring); portfolio-wide rollout.",
     "KPI targets trending to Section 8 levels; monitoring triggers live for all new originations."],
  ].map(
    (r) =>
      new TableRow({
        children: r.map((t, i) =>
          cell(cellP(t, i === 0 ? { bold: true } : { size: 20 }), {
            width: { size: widths[i], type: WidthType.DXA },
          }),
        ),
      }),
  );
  return new Table({
    width: { size: TEXT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [new TableRow({ children: header, tableHeader: true }), ...rows],
  });
};

// ---------- content ----------
const children = [];

// Cover
children.push(
  para(run("MORTGAGE ORIGINATION", { bold: true, size: 56, color: palette.dark }), {
    alignment: AlignmentType.CENTER,
    spacing: { before: 2600, after: 0 },
  }),
  para(run("PROCESS AUDIT", { bold: true, size: 56, color: palette.dark }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
  }),
  para(
    run("Pain-Point Analysis and Agentic AI / GenAI Solution Mapping", {
      size: 30,
      color: palette.teal,
    }),
    { alignment: AlignmentType.CENTER, spacing: { after: 120 } },
  ),
  para(run("Retail Banking — End-to-End Lending Process", { size: 24, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 900 },
  }),
  para(run("BASELINE EDITION", { bold: true, size: 26, color: palette.high }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
  }),
  para(
    run(
      "Built on an industry-typical process model. To be recalibrated against the client's procedure, process map and system landscape (see Appendix A).",
      { size: 20, color: palette.light, italics: true },
    ),
    { alignment: AlignmentType.CENTER, spacing: { after: 1600 } },
  ),
  para(run("17 November 2026", { size: 22, color: palette.primary }), {
    alignment: AlignmentType.CENTER,
  }),
  pageBreak(),
);

// TOC
children.push(
  para(run("Contents", { bold: true, size: 30, color: palette.dark }), {
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 240, after: 120 },
  }),
  para(
    run("Right-click the table and choose “Update Field” to refresh page numbers.", {
      italics: true,
      color: palette.light,
      size: 19,
    }),
  ),
  toc([
    { title: "1. Executive Summary", level: 1, page: 3 },
    { title: "2. Audit Scope, Method and Baseline Assumptions", level: 1, page: 5 },
    { title: "3. Process Model", level: 1, page: 7 },
    { title: "4. Pain-Point Register", level: 1, page: 9 },
    { title: "5. Agentic AI / GenAI Solution Mapping", level: 1, page: 16 },
    { title: "6. Regulatory and Compliance Guardrails", level: 1, page: 21 },
    { title: "7. Prioritisation and Roadmap", level: 1, page: 23 },
    { title: "8. KPI Framework", level: 1, page: 25 },
    { title: "Appendix A. Recalibration Checklist", level: 1, page: 26 },
    { title: "Appendix B. Scoring Definitions", level: 1, page: 27 },
  ]),
  pageBreak(),
);

// 1. Executive summary
children.push(
  h1("1. Executive Summary"),
  body(
    T`This report audits the end-to-end retail mortgage origination process — from application intake to servicing handover — and maps every identified gap to a concrete agentic AI or GenAI solution. It is a baseline edition: the findings are derived from an industry-typical mortgage process model, and each one is structured so it can be confirmed, re-scored or removed once the client's own procedure documentation and process map are supplied.`,
  ),
  body(
    T`The audit decomposed the process into 8 stages and identified 27 distinct pain points: 6 Critical, 14 High and 7 Medium. The pain is not evenly distributed — it concentrates in three areas: document collection and verification, income and affordability verification, and the clerical workload surrounding the underwriting decision.`,
  ),
  para([
    run("The single most important structural conclusion: ", { bold: true }),
    run(
      "the process does not suffer from a lack of rules or people — it suffers from manual data movement and unstructured communication. The same data is re-keyed between systems four to six times across the lifecycle of one file; exceptions escape into email; and expert staff spend most of their time assembling information rather than judging it.",
    ),
  ]),
  body(
    T`The report proposes eight solution blocks (A–H). Three are quick wins deliverable within two to six months — document intelligence, smart intake, and offer/disbursement automation. The underwriting copilot is the highest-impact strategic investment: it removes the clerical workload around the decision while keeping the credit decision itself firmly human, which is both a regulatory requirement and good practice. All solutions are specified with explicit human-in-the-loop boundaries, an architecture sketch, and measurable KPIs.`,
  ),
  body(
    T`Directionally, full implementation targets a reduction in time-to-decision from a typical 10–20 working days to 3–7, near-elimination of manual data entry, straight-through processing of 30–50% of simple cases, and a step change in audit and fraud readiness. These are targets to be validated against actual baseline metrics during recalibration, not commitments.`,
  ),
);

// 2. Scope & method
children.push(
  pageBreak(),
  h1("2. Audit Scope, Method and Baseline Assumptions"),
  h2("2.1 Scope"),
  body(
    T`The audit covers the retail mortgage origination value stream end to end: application intake, document collection and verification, KYC/AML and identity, credit scoring and affordability, property valuation and collateral, underwriting and decision, offer/signing/disbursement, and the handover into early servicing. Ancillary processes (marketing, pricing committees, treasury funding, collections strategy) are out of scope except where they consume outputs of the audited process.`,
  ),
  h2("2.2 Method"),
  body(T`Four analytical passes were applied to each process step:`),
  bullet(T`Decomposition — every step broken down to actor, system touched, data moved, and decision made. Manual data movement between systems is the primary pain signal.`),
  bullet(T`Failure-mode analysis — for each step: what can go wrong, what happens when the input is late/wrong/missing, and whether the documented procedure covers the exception or abandons the file to improvisation.`),
  bullet(T`Compliance screening — each step checked against audit-trail, data-protection and credit-decisioning expectations (GDPR, EBA loan-origination guidelines, EU AI Act risk classes).`),
  bullet(T`Automation-fit scoring — each pain point scored for expected impact (1–10) and implementation effort (1–10), then clustered into solution blocks where one capability removes several pain points at once.`),
  h2("2.3 Baseline assumptions and recalibration"),
  body(
    T`This edition assumes an industry-typical mid-size retail bank: a loan origination system (LOS) that is partially integrated, documents exchanged largely by email, credit policy partially hardcoded, and limited straight-through processing. Where the client's reality differs, findings will be re-scored — some will disappear, new ones will appear, and severities will shift. Appendix A lists exactly what to provide and how each finding is re-evaluated. No finding in this report should be treated as confirmed against the client's environment until that pass is done.`,
  ),
);

// 3. Process model
children.push(
  pageBreak(),
  h1("3. Process Model"),
  body(
    T`The baseline process comprises eight stages. The table summarises actors, systems and typical cycle times observed in comparable retail banks; Figure 1 shows where the audited pain concentrates.`,
  ),
  stageTable(),
  para(run("Table 1 — Baseline process model: stages, actors, systems and cycle times.", { italics: true, size: 19, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 200 },
  }),
  img("fig1_process_heatmap.png", 595, 198),
  caption("Figure 1 — Process flow coloured by the severity of the worst finding in each stage."),
  body(
    T`Two structural properties of this model drive most of the downstream pain. First, data enters the process in unstructured form (documents, emails, PDFs) and is converted to structured data by hand — repeatedly, at every stage boundary. Second, the procedure documents the happy path thoroughly and the exception paths barely at all, so everything non-standard flows into email threads and personal knowledge.`,
  ),
);

// 4. Pain-point register
children.push(
  pageBreak(),
  h1("4. Pain-Point Register"),
  body(
    T`27 findings were recorded across the eight stages. Severity reflects the combination of financial impact, regulatory exposure and frequency (definitions in Appendix B). Table 2 is the summary register; Sections 4.1–4.8 give each finding with its root cause and typical symptom.`,
  ),
  img("fig2_findings_by_stage.png", 557, 306),
  caption("Figure 2 — Findings per stage by severity."),
  findingsSummaryTable(),
  para(run("Table 2 — Pain-point summary register.", { italics: true, size: 19, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 160 },
  }),
);

DATA.stages.forEach((stage, idx) => {
  const findings = DATA.findings.filter((f) => f.stage === stage.id);
  children.push(h2(`4.${idx + 1} ${stage.name}`));
  for (const f of findings) {
    children.push(
      para(
        [
          run(`${f.id} — ${f.title} `, { bold: true }),
          run(`[${f.severity} · ${f.category}]`, { bold: true, color: sevColor(f.severity) }),
        ],
        { spacing: { before: 140, after: 60 } },
      ),
      para([run("Root cause: ", { bold: true, size: 21 }), run(f.root, { size: 21 })], {
        indent: { left: convertInchesToTwip(0.25) },
        spacing: { after: 40 },
      }),
      para([run("Typical symptom: ", { bold: true, size: 21 }), run(f.symptom, { size: 21 })], {
        indent: { left: convertInchesToTwip(0.25) },
        spacing: { after: 120 },
      }),
    );
  }
});

// 5. Solutions
children.push(
  pageBreak(),
  h1("5. Agentic AI / GenAI Solution Mapping"),
  body(
    T`The 27 findings cluster into eight solution blocks. The clustering principle: one shared capability (e.g. document intelligence) removes pain points in several stages at once, so solutions are designed around capabilities, not around process steps. Each solution specifies what the agent does, where humans stay in the loop, the architecture sketch, and the KPIs that prove it works. Impact and effort scores position each block on the priority matrix in Figure 3.`,
  ),
  img("fig3_priority_matrix.png", 528, 366),
  caption("Figure 3 — Priority matrix: expected impact vs. implementation effort."),
);

DATA.solutions.forEach((s) => {
  children.push(
    h2(`5.${s.id} Solution ${s.id} — ${s.name}`),
    para([run("Addresses findings: ", { bold: true }), run(s.addresses)]),
    para([run("What it does: ", { bold: true }), run(s.desc)]),
    para([run("Human-in-the-loop boundary: ", { bold: true }), run(s.hitl)]),
    para([run("Architecture sketch: ", { bold: true }), run(s.architecture)]),
    para([run("KPIs: ", { bold: true }), run(s.kpis)]),
    para(
      [
        run("Scoring: ", { bold: true }),
        run(`impact ${s.impact}/10, effort ${s.effort}/10.`),
      ],
      { spacing: { after: 200 } },
    ),
  );
});

children.push(
  body(
    T`A note on what is deliberately not proposed: fully automated credit approval. Solutions D and F automate everything around the decision — evidence gathering, verification, policy pre-checks, rationale drafting — but the decision on a natural person's creditworthiness stays with a human underwriter, supported rather than replaced. This is driven by GDPR Article 22 constraints on solely automated decisions, the EU AI Act's high-risk classification of credit scoring, and simple model-risk prudence.`,
  ),
);

// 6. Regulatory
children.push(
  pageBreak(),
  h1("6. Regulatory and Compliance Guardrails"),
  body(
    T`Every solution in Section 5 operates inside a regulated credit process. The guardrails below are design constraints, not afterthoughts — they shape the architecture of each agent.`,
  ),
  h2("6.1 Automated decision-making (GDPR Art. 22)"),
  body(
    T`Credit decisions about natural persons generally cannot be based solely on automated processing with legal or similarly significant effect, absent narrow exceptions. The designs therefore keep a human decision-maker accountable for every approval and decline; agents prepare, verify and document. Where the client's legal team confirms a lawful automation basis exists for a specific segment (e.g. pre-approved limit increases for existing customers), a bounded auto-decision path can be added later — it is not part of this baseline.`,
  ),
  h2("6.2 EU AI Act — credit scoring is high-risk"),
  body(
    T`AI systems used to evaluate creditworthiness of natural persons are classified as high-risk under the EU AI Act. This brings obligations around risk management, data governance, technical documentation, logging, transparency, human oversight and accuracy monitoring. The proposed architecture treats these as features: every agent writes structured, timestamped evidence; every model output carries confidence and provenance; human oversight points are explicit workflow states, not conventions.`,
  ),
  h2("6.3 Loan origination and creditworthiness assessment"),
  body(
    T`Supervisory expectations (e.g. EBA Guidelines on loan origination and monitoring) require sound borrower assessment, documented affordability analysis and anti-fraud controls. Solutions A and D directly strengthen these: consistent document fraud screening on 100% of files, verified income from primary data sources, and affordability computed by a governed, versioned engine rather than divergent spreadsheets.`,
  ),
  h2("6.4 Audit trail and model risk"),
  body(
    T`Each agent operates under the bank's model risk management framework: inventory registration, validation before production, drift monitoring, and a documented override path. The evidence store is append-only: what the agent saw, what it extracted, what confidence it assigned, what the human decided. This turns today's weakest compliance points (PP-09, PP-10, PP-20) into the strongest.`,
  ),
  h2("6.5 Data protection in agent pipelines"),
  body(
    T`Documents and extracted data carry purpose limitation: data collected for the mortgage file is processed only for that purpose, retention follows the existing schedule, and LLM components run under the bank's data-processing agreements with no training on customer data. Extraction results are stored as structured data with source links, not as free-floating model context.`,
  ),
);

// 7. Roadmap
children.push(
  pageBreak(),
  h1("7. Prioritisation and Roadmap"),
  body(
    T`Sequencing follows the priority matrix (Figure 3): quick wins first to fund the programme with early results, then the core credit capabilities, then the connective tissue. The roadmap assumes a phased rollout over roughly 18 months with measurable exit criteria per phase.`,
  ),
  roadmapTable(),
  para(run("Table 3 — Implementation roadmap with exit criteria.", { italics: true, size: 19, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 160 },
  }),
  body(
    T`Dependencies worth noting: Solutions D and F depend on the canonical data model from Phase 0 and benefit from the extraction pipeline delivered by Solution A in Phase 1. Solution C (perpetual KYC) requires cross-product data access agreements that typically need longer lead time — start those conversations in Phase 0 even though delivery lands in Phase 3.`,
  ),
);

// 8. KPI
children.push(
  pageBreak(),
  h1("8. KPI Framework"),
  body(
    T`The programme is judged on operational, risk and customer metrics, measured against a baseline captured in Phase 0. The targets below are directional ranges from comparable implementations — they must be re-based on actual client data before becoming commitments.`,
  ),
  kpiTable(),
  para(run("Table 4 — KPI framework with directional targets.", { italics: true, size: 19, color: palette.light }), {
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 160 },
  }),
  body(
    T`Measurement discipline matters more than the targets themselves: every KPI needs a named owner, a data source agreed with finance/risk, and a baseline captured before the first pilot goes live. Several baselines above (rework loops, approval-to-disbursement leakage) are typically unmeasured today — capturing them is itself a Phase 0 deliverable.`,
  ),
);

// Appendix A
children.push(
  pageBreak(),
  h1("Appendix A. Recalibration Checklist"),
  body(
    T`To convert this baseline into a client-specific audit, provide the following. Each input maps to a specific recalibration action.`,
  ),
  bullet(T`Procedure / SOP document(s) — every finding is checked against the documented flow: confirmed, re-scored, or removed; undocumented workarounds mentioned in interviews are added as new findings.`),
  bullet(T`Process map (BPMN, flowchart, Visio, even a photo of a whiteboard) — cross-checked against the procedure; every disagreement between the two is itself a finding, because it marks where the process actually lives in people's heads.`),
  bullet(T`Source code or system documentation for the LOS/workflow/integrations — enables the code-level pass: hardcoded policy rules, point-to-point integration fragility, missing idempotency and error handling, shadow data stores.`),
  bullet(T`Volumes and metrics — applications per month, time-to-decision distribution, rework/withdrawal rates, staffing per stage; used to quantify severity and replace directional KPI targets with real baselines.`),
  bullet(T`Systems inventory and org chart — which systems are touched at each stage and which teams own them; drives integration effort scores.`),
  bullet(T`Known incidents — past audit findings, fraud cases, complaints, regulator feedback; calibrates severity against what has actually hurt.`),
  body(
    T`Recalibration output: a revised edition of this report with confirmed findings, client-specific severities, quantified impact estimates, and a roadmap adjusted to the client's actual systems and constraints.`,
  ),
);

// Appendix B
children.push(
  pageBreak(),
  h1("Appendix B. Scoring Definitions"),
  h2("Severity"),
  bullet(T`Critical — direct financial loss, regulatory breach potential, or a step that routinely blocks or silently corrupts the process. Fix first regardless of effort.`),
  bullet(T`High — significant recurring cost, delay or risk; customers and staff feel it weekly.`),
  bullet(T`Medium — friction worth removing; rarely fatal, consistently annoying, occasionally masking bigger issues.`),
  h2("Impact (solution scoring, 1–10)"),
  body(
    T`Composite of cycle-time reduction, cost-to-serve reduction, risk reduction and customer experience, weighted toward the pain points the solution removes (severity-weighted count) and the breadth of stages it touches.`,
  ),
  h2("Effort (solution scoring, 1–10)"),
  body(
    T`Composite of integration complexity with existing systems, data readiness, regulatory validation lead time, and organisational change required. A 3–4 is a contained pilot with existing APIs; a 6–7 touches core credit infrastructure and needs formal model validation.`,
  ),
);

// ---------- document ----------
const doc = new Document({
  features: { updateFields: true },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "\u2022",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 560, hanging: 280 } } },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        titlePage: true,
        page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      },
      headers: {
        first: new Header({ children: [para(run(""))] }),
        default: new Header({
          children: [
            para(
              run("Mortgage Origination Process Audit — Baseline Report", {
                size: 18,
                color: palette.light,
              }),
              {
                alignment: AlignmentType.RIGHT,
                border: {
                  bottom: { style: BorderStyle.SINGLE, size: 4, color: palette.border },
                },
              },
            ),
          ],
        }),
      },
      footers: {
        first: new Footer({ children: [para(run(""))] }),
        default: new Footer({
          children: [
            para(new TextRun({ children: [PageNumber.CURRENT], font, size: 18 }), {
              alignment: AlignmentType.CENTER,
            }),
          ],
        }),
      },
      children,
    },
  ],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(doc));
