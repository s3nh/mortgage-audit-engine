"""Generate audit charts for the mortgage process audit report."""
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)

with open(os.path.join(ROOT, "audit_data.json"), encoding="utf-8") as f:
    DATA = json.load(f)

SEV_COLORS = {"Critical": "#8E3B2F", "High": "#C07A3E", "Medium": "#D0B45C"}
STAGE_SHORT = [s["short"] for s in DATA["stages"]]
STAGE_NAMES = [s["name"] for s in DATA["stages"]]

# ---------- Fig 1: process flow heatmap (single row) ----------
fig, ax = plt.subplots(figsize=(12.4, 2.6), dpi=200)
n = len(DATA["stages"])
ax.set_xlim(0, n * 12.5); ax.set_ylim(0, 16); ax.axis("off")

bw, bh = 11.0, 8.5
sev_rank = {"Critical": 3, "High": 2, "Medium": 1}
for i, stage in enumerate(DATA["stages"]):
    findings = [f for f in DATA["findings"] if f["stage"] == stage["id"]]
    worst = max((sev_rank[f["severity"]] for f in findings), default=0)
    color = {3: "#8E3B2F", 2: "#C07A3E", 1: "#D0B45C", 0: "#78909C"}[worst]
    x, y = i * 12.5 + 0.3, 3.5
    box = FancyBboxPatch((x, y), bw, bh, boxstyle="round,pad=0.3",
                         linewidth=0, facecolor=color, alpha=0.92)
    ax.add_patch(box)
    ax.text(x + bw / 2, y + bh * 0.68, stage["short"], ha="center", va="center",
            fontsize=8.2, color="white", fontweight="bold")
    ax.text(x + bw / 2, y + bh * 0.28,
            f"{len(findings)} findings", ha="center", va="center",
            fontsize=7.4, color="white")
    if i < n - 1:
        ax.add_patch(FancyArrowPatch((x + bw + 0.15, y + bh / 2),
                                     (x + bw + 1.1, y + bh / 2),
                                     arrowstyle="-|>", mutation_scale=12,
                                     color="#37474F", linewidth=1.3))

handles = [plt.Rectangle((0, 0), 1, 1, facecolor=c, alpha=0.92)
           for c in SEV_COLORS.values()]
ax.legend(handles, [f"Worst severity: {k}" for k in SEV_COLORS],
          loc="lower center", ncol=3, frameon=False, fontsize=8,
          bbox_to_anchor=(0.5, -0.42))
fig.suptitle("Retail mortgage origination: pain-point severity concentrates in documents, income and underwriting",
             fontsize=11.5, fontweight="bold", color="#263238", y=0.99)
fig.savefig(os.path.join(ASSETS, "fig1_process_heatmap.png"),
            bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------- Fig 2: findings by stage & severity ----------
stages = DATA["stages"]
counts = {sev: [sum(1 for f in DATA["findings"]
                    if f["stage"] == s["id"] and f["severity"] == sev)
                for s in stages] for sev in ["Critical", "High", "Medium"]}

fig, ax = plt.subplots(figsize=(9.6, 4.4), dpi=200)
x = range(len(stages))
bottom = [0] * len(stages)
for sev in ["Critical", "High", "Medium"]:
    vals = counts[sev]
    ax.bar(x, vals, bottom=bottom, color=SEV_COLORS[sev], width=0.62,
           label=sev, edgecolor="white", linewidth=0.6)
    for xi, (v, b) in enumerate(zip(vals, bottom)):
        if v:
            ax.text(xi, b + v / 2, str(v), ha="center", va="center",
                    fontsize=8, color="white", fontweight="bold")
    bottom = [b + v for b, v in zip(bottom, vals)]
ax.set_xticks(list(x))
ax.set_xticklabels(STAGE_SHORT, fontsize=8, rotation=18, ha="right")
ax.set_ylabel("Number of findings", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, fontsize=9)
ax.set_title("27 findings across 8 stages — High-severity items dominate",
             fontsize=11.5, fontweight="bold", color="#263238", pad=12)
fig.savefig(os.path.join(ASSETS, "fig2_findings_by_stage.png"),
            bbox_inches="tight", facecolor="white")
plt.close(fig)

# ---------- Fig 3: priority matrix (impact vs effort) ----------
fig, ax = plt.subplots(figsize=(8.8, 6.2), dpi=200)
sol = DATA["solutions"]
colors = ["#2E6E63", "#8E3B2F", "#37474F", "#C07A3E",
          "#5C6B73", "#7A5C8E", "#A07840", "#4A6572"]
ax.axhline(7.5, color="#B0BEC5", lw=1, ls="--")
ax.axvline(5.0, color="#B0BEC5", lw=1, ls="--")
label_pos = {
    "A": (0.14, 0.14, "left"),
    "B": (-0.14, 0.0, "right"),
    "C": (0.14, 0.14, "left"),
    "D": (0.16, 0.16, "left"),
    "E": (-0.14, 0.0, "right"),
    "F": (0.16, 0.0, "left"),
    "G": (-0.14, 0.0, "right"),
    "H": (0.14, -0.05, "left"),
}
for s, c in zip(sol, colors):
    ax.scatter(s["effort"], s["impact"], s=340, color=c, alpha=0.9,
               edgecolor="white", linewidth=1.4, zorder=3)
    dx, dy, ha = label_pos[s["id"]]
    ax.annotate(f'{s["id"]}. {s["short"]}', (s["effort"], s["impact"]),
                xytext=(s["effort"] + dx, s["impact"] + dy),
                fontsize=8.2, color="#263238", ha=ha, va="center")
ax.text(1.6, 9.6, "QUICK WINS", fontsize=10, fontweight="bold", color="#2E6E63")
ax.text(7.6, 9.6, "STRATEGIC BETS", fontsize=10, fontweight="bold", color="#37474F")
ax.text(1.6, 4.15, "FILL-INS", fontsize=10, fontweight="bold", color="#78909C")
ax.text(7.0, 4.15, "DEPRIORITIZE / PHASE LATER", fontsize=10,
        fontweight="bold", color="#78909C")
ax.set_xlim(0.5, 9.5); ax.set_ylim(3.5, 10.3)
ax.set_xlabel("Implementation effort (1 = trivial, 10 = major program)", fontsize=9)
ax.set_ylabel("Expected impact (1 = marginal, 10 = transformational)", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Document intelligence leads the quick wins; the underwriting copilot is the top strategic bet",
             fontsize=11, fontweight="bold", color="#263238", pad=12)
fig.savefig(os.path.join(ASSETS, "fig3_priority_matrix.png"),
            bbox_inches="tight", facecolor="white")
plt.close(fig)

print("charts done:", os.listdir(ASSETS))
