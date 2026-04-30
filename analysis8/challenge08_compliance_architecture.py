"""
Challenge 8: The Compliance Architecture Spectrum
AMC Research Sprint — April 2026

Outputs (analysis8/figures/):
  fig1_compliance_overview.png          — overall distribution + by weapon category
  fig2_compliance_over_time.png         — annotated time series (area chart)
  fig3_treaty_examples.png              — tier examples table
  fig4_risk_compliance_framework.png    — risk × compliance matrix
  fig4b_empirical_risk_groups.png       — compliance shares by empirical risk group
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import numpy as np
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIG_DIR  = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

# ── Design system ─────────────────────────────────────────────────────────────
PALETTE = {
    "navy":      "#1B2A4A",
    "red":       "#E63946",
    "steel":     "#457B9D",
    "teal":      "#2A9D8F",
    "gold":      "#E9C46A",
    "offwhite":  "#F8F9FA",
    "mid_gray":  "#8E9AAA",
    "light_gray":"#DEE2E6",
}
TIER_COLORS = {
    "No mechanism":            "#CBD5E0",
    "Consultation only":       "#F6AD55",
    "Demonstrated compliance": "#457B9D",
    "Verified compliance":     "#1B2A4A",
}
TIER_ORDER = ["No mechanism", "Consultation only",
              "Demonstrated compliance", "Verified compliance"]

plt.rcParams.update({
    "font.family":       "sans-serif",
    "font.sans-serif":   ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.titlesize":    14,
    "axes.titleweight":  "bold",
    "axes.labelsize":    11,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
})

# ── Load data ──────────────────────────────────────────────────────────────────
info    = pd.read_csv(DATA_DIR / "amcdata_agreement_info_V2.csv",     encoding="latin1")
weapons = pd.read_csv(DATA_DIR / "amcdata_weapons_facilities_V2.csv", encoding="latin1")

# ── Compliance score ──────────────────────────────────────────────────────────
def compliance_level(row):
    if row.get("verified_compliance_mechanism",    0) == 1: return 3
    if row.get("demonstrated_compliance_mechanism",0) == 1: return 2
    if row.get("consultation_mechanism",           0) == 1: return 1
    return 0

info["compliance_score"] = info.apply(compliance_level, axis=1)
LABELS = {0:"No mechanism",1:"Consultation only",
          2:"Demonstrated compliance",3:"Verified compliance"}
info["compliance_label"] = info["compliance_score"].map(LABELS)
info["decade"] = (info["year"] // 10) * 10

# ── Weapon category lookup (use summary_category flag, not string filter) ─────
summary_rows = (
    weapons[weapons["summary_category"] == 1][["agreement_id","item"]]
    .drop_duplicates().copy()
)
summary_rows["item"] = summary_rows["item"].str.strip()
extracted = summary_rows["item"].str.extract(r"\((.+)\)")
summary_rows["weapon_cat"] = extracted[0].where(extracted[0].notna(),
                                                 summary_rows["item"])
merged = info.merge(summary_rows, on="agreement_id", how="left")

score_by_cat = (
    merged.dropna(subset=["weapon_cat"])
    .groupby("weapon_cat")["compliance_score"]
    .mean().sort_values(ascending=False).round(2)
)


def empirical_group(mean_score):
    if pd.isna(mean_score):
        return np.nan
    if mean_score >= 2.5:
        return "High-compliance weapon domains"
    return "Medium-compliance weapon domains"


cat_empirical_group = score_by_cat.apply(empirical_group).to_dict()
summary_rows["empirical_group"] = summary_rows["weapon_cat"].map(cat_empirical_group)
agreement_group = (
    summary_rows.dropna(subset=["empirical_group"])
    .assign(
        group_rank=lambda df: df["empirical_group"].map(
            {
                "General / unclassified agreements": 0,
                "Medium-compliance weapon domains": 1,
                "High-compliance weapon domains": 2,
            }
        )
    )
    .sort_values(["agreement_id", "group_rank"])
    .groupby("agreement_id")
    .tail(1)[["agreement_id", "empirical_group"]]
)

# ── Rename categories for display ─────────────────────────────────────────────
RENAME = {
    "Conventional Weapons Land":  "Conv. Land",
    "Conventional Weapons Air":   "Conv. Air",
    "Conventional Weapons Sea":   "Conv. Sea",
    "Nuclear Weapons":            "Nuclear Weapons",
    "Nuclear Missiles":           "Nuclear Missiles",
    "Biological Weapons":         "Biological Weapons",
    "Chemical Weapons":           "Chemical Weapons",
    "Heavy Bombers":              "Heavy Bombers",
    "ICBM Launchers":             "ICBM Launchers",
    "ICBMs":                      "ICBMs",
    "SLBM Launchers":             "SLBM Launchers",
    "SLBMs":                      "SLBMs",
    "Nuclear Submarines":         "Nuclear Submarines",
}

# =============================================================================
# FIGURE 1  ── Compliance overview (2 panels)
#   Left:  donut chart — overall distribution
#   Right: horizontal stacked bars — by weapon category
# =============================================================================
cat_df = (
    merged.dropna(subset=["weapon_cat"])
    .groupby(["weapon_cat","compliance_label"])["agreement_id"]
    .nunique().unstack(fill_value=0)
)
for lbl in TIER_ORDER:
    if lbl not in cat_df.columns: cat_df[lbl] = 0
cat_df = cat_df[TIER_ORDER]
cat_df.index = [RENAME.get(x, x) for x in cat_df.index]
cat_df["total"] = cat_df.sum(axis=1)
cat_df = cat_df.sort_values("Verified compliance", ascending=True)

fig1 = plt.figure(figsize=(20, 7.4))
gs   = gridspec.GridSpec(1, 2, width_ratios=[1, 2.8], figure=fig1, wspace=0.14)

# ── Left: donut ────────────────────────────────────────────────────────────────
ax_d = fig1.add_subplot(gs[0])
dist = info["compliance_label"].value_counts().reindex(TIER_ORDER, fill_value=0)
wedge_colors = [TIER_COLORS[l] for l in dist.index]
wedges, _ = ax_d.pie(
    dist.values, colors=wedge_colors,
    startangle=90, counterclock=False,
    wedgeprops=dict(width=0.52, edgecolor="white", linewidth=2.5),
)
total_n = len(info)
ax_d.text(0, 0.05,  str(total_n),  ha="center", fontsize=26,
          fontweight="bold", color=PALETTE["navy"])
ax_d.text(0, -0.22, "agreements",  ha="center", fontsize=10,
          color=PALETTE["mid_gray"])

# Custom legend inside the donut area
for i, (lbl, n) in enumerate(zip(dist.index, dist.values)):
    y_pos = 1.28 - i * 0.32
    ax_d.plot(-1.35, y_pos, "o", color=TIER_COLORS[lbl], markersize=10,
              transform=ax_d.transData, clip_on=False)
    ax_d.text(-1.20, y_pos, lbl,    fontsize=9,  va="center",
              color=PALETTE["navy"], transform=ax_d.transData, clip_on=False)
    ax_d.text( 1.20, y_pos, f"{n} ({n/total_n:.0%})",
              fontsize=9, va="center", ha="right",
              color=PALETTE["mid_gray"], transform=ax_d.transData, clip_on=False,
              fontweight="bold")

ax_d.set_title("Overall Distribution\n128 Arms Control Agreements",
               fontsize=12, fontweight="bold", color=PALETTE["navy"], pad=18)

# ── Right: horizontal stacked bars ────────────────────────────────────────────
ax_b = fig1.add_subplot(gs[1])
ax_b.set_facecolor(PALETTE["offwhite"])

y_pos = np.arange(len(cat_df))
left  = np.zeros(len(cat_df))
for lbl in TIER_ORDER:
    vals = cat_df[lbl].values
    bars = ax_b.barh(y_pos, vals, left=left, color=TIER_COLORS[lbl],
                     height=0.62, edgecolor="white", linewidth=1)
    for xi, (v, l) in enumerate(zip(vals, left)):
        if v >= 1:
            ax_b.text(l + v/2, xi, str(int(v)),
                      ha="center", va="center", fontsize=8,
                      color="white" if lbl != "No mechanism" else "#555",
                      fontweight="bold")
    left += vals

# Mean score dots on a twin axis
ax_twin = ax_b.twiny()
ax_twin.set_xlim(0, 3.5)
ax_twin.set_xlabel("Mean compliance score  (0–3)", fontsize=9,
                   color=PALETTE["steel"], labelpad=6)
ax_twin.tick_params(colors=PALETTE["steel"], labelsize=8)
raw_cats = [next((k for k,v in RENAME.items() if v==c), c.replace("\n"," "))
            for c in cat_df.index]
scores = [score_by_cat.get(rc, np.nan) for rc in raw_cats]
ax_twin.plot(scores, y_pos, "D", color=PALETTE["red"],
             markersize=7, zorder=5, clip_on=False)
for xi, sc in enumerate(scores):
    if not np.isnan(sc):
        ax_twin.text(sc + 0.08, xi, f"{sc:.2f}",
                     va="center", fontsize=7.5, color=PALETTE["red"], fontweight="bold")

ax_b.set_yticks(y_pos)
ax_b.set_yticklabels(cat_df.index, fontsize=9.5, color=PALETTE["navy"])
ax_b.set_xlabel("Number of agreements", fontsize=10)
ax_b.set_xlim(0, cat_df["total"].max() * 1.12)
ax_b.set_title("Compliance Architecture by Weapon Category\n",
               fontsize=12, fontweight="bold", color=PALETTE["navy"])
ax_b.spines[["left","bottom"]].set_visible(True)
ax_b.spines["left"].set_color(PALETTE["light_gray"])
ax_b.spines["bottom"].set_color(PALETTE["light_gray"])

# Key callout
ax_b.annotate(
    "Strategic nuclear &\nCBRN: mean = 3.0",
    xy=(0.5, len(cat_df)-0.5), xytext=(cat_df["total"].max()*0.55, len(cat_df)-0.7),
    fontsize=8.5, color=PALETTE["red"], fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=PALETTE["red"], lw=1.3),
    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=PALETTE["red"], lw=1),
)

fig1.suptitle("The Compliance Architecture Spectrum in Arms Control",
              fontsize=16, fontweight="bold", color=PALETTE["navy"], y=1.01)

fig1.savefig(FIG_DIR / "fig1_compliance_overview.png", dpi=160,
             bbox_inches="tight", facecolor="white")
plt.close(fig1)
print("Saved: fig1_compliance_overview.png")

# =============================================================================
# FIGURE 2  ── Compliance over time — stacked area + key annotations
# =============================================================================
decade_df = (
    info.groupby(["decade","compliance_label"])["agreement_id"]
    .count().unstack(fill_value=0)
)
for lbl in TIER_ORDER:
    if lbl not in decade_df.columns: decade_df[lbl] = 0
decade_df = decade_df[TIER_ORDER][decade_df.index >= 1920]

fig2, ax = plt.subplots(figsize=(14, 6))

x = decade_df.index.astype(int)
cumulative = np.zeros(len(x))
fills = []
for lbl in TIER_ORDER:
    vals = decade_df[lbl].values
    ax.bar(x, vals, bottom=cumulative, color=TIER_COLORS[lbl],
           width=7, edgecolor="white", linewidth=0.8, label=lbl, zorder=2)
    # Value labels inside bars
    for xi, (v, bot) in enumerate(zip(vals, cumulative)):
        if v > 0:
            ax.text(x[xi], bot + v/2, str(int(v)), ha="center", va="center",
                    fontsize=8.5, fontweight="bold",
                    color="white" if lbl != "No mechanism" else "#555",
                    zorder=3)
    cumulative += vals

totals = cumulative
# Verified-compliance line on twin axis
verified_vals = decade_df["Verified compliance"].values
ax2 = ax.twinx()
ax2.plot(x, verified_vals, "o-", color=PALETTE["red"],
         linewidth=2.5, markersize=8, zorder=4, label="Verified (count)")
ax2.set_ylabel("Verified compliance agreements", fontsize=10,
               color=PALETTE["red"], labelpad=8)
ax2.tick_params(axis="y", colors=PALETTE["red"], labelsize=9)
ax2.set_ylim(0, max(verified_vals)*2.2 or 2)
ax2.spines["right"].set_visible(True)
ax2.spines["right"].set_color(PALETTE["red"])
ax2.spines["top"].set_visible(False)

# Shading — Cold War era
ax.axvspan(1947, 1991, alpha=0.06, color=PALETTE["navy"], zorder=0)
ax.text(1955, totals.max()*1.01, "Cold War era",
        fontsize=8.5, color=PALETTE["navy"], alpha=0.6, style="italic")

# Annotations
peak_x = 1990
peak_idx = list(x).index(peak_x)
ax.annotate(
    "Peak: 1970s–1990s\nCold War arms control surge\n(SALT, INF, START, CWC, CFE)",
    xy=(peak_x, totals[peak_idx]),
    xytext=(peak_x - 22, totals.max()*0.82),
    fontsize=8.5, color=PALETTE["navy"], fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=PALETTE["navy"], lw=1.3),
    bbox=dict(boxstyle="round,pad=0.4", fc="#E8F4F8", ec=PALETTE["navy"], lw=1),
)

post_x = 2000
post_idx = list(x).index(post_x)
ax.annotate(
    "Post-2000:\nZero new verified compliance\nagreements in 2000s",
    xy=(post_x, totals[post_idx]),
    xytext=(post_x + 5, totals.max()*0.72),
    fontsize=8.5, color=PALETTE["red"], fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=PALETTE["red"], lw=1.3),
    bbox=dict(boxstyle="round,pad=0.4", fc="#FDEEEE", ec=PALETTE["red"], lw=1),
)

ax.set_xticks(x)
ax.set_xticklabels([f"{int(d)}s" for d in x], fontsize=10)
ax.set_ylabel("Number of agreements", fontsize=11)
ax.set_xlabel("Decade", fontsize=11)
ax.set_ylim(0, totals.max() * 1.22)
ax.set_xlim(x[0] - 6, x[-1] + 10)

# Legend
handles = [mpatches.Patch(color=TIER_COLORS[l], label=l) for l in TIER_ORDER]
handles.append(plt.Line2D([0],[0], color=PALETTE["red"], marker="o",
                           linewidth=2, markersize=7, label="Verified (line)"))
ax.legend(handles=handles, fontsize=8.5, frameon=True, framealpha=0.95,
          loc="upper left", edgecolor=PALETTE["light_gray"])

ax.set_title("Compliance Architecture Over Time (1920s–2010s)\n"
             "The verified-compliance peak was built during a specific geopolitical window — and has not been rebuilt",
             fontsize=13, fontweight="bold", color=PALETTE["navy"], pad=12)

fig2.tight_layout()
fig2.savefig(FIG_DIR / "fig2_compliance_over_time.png", dpi=160,
             bbox_inches="tight", facecolor="white")
plt.close(fig2)
print("Saved: fig2_compliance_over_time.png")

# =============================================================================
# FIGURE 3  ── Treaty examples — clean card-style table
# =============================================================================
EXAMPLES = [
    {
        "tier": "No mechanism",
        "treaty": "Genocide Convention",
        "year": "1948",
        "mechanism": "States pledge non-commission of genocide.",
        "limitation": "No reporting, inspection, or review body.",
    },
    {
        "tier": "Consultation only",
        "treaty": "Antarctic Treaty",
        "year": "1959",
        "mechanism": "Annual Consultative Meetings discuss compliance concerns.",
        "limitation": "Discussion only; no binding checks or observer.",
    },
    {
        "tier": "Demonstrated compliance",
        "treaty": "Ottawa Mine Ban Treaty",
        "year": "1997",
        "mechanism": "States submit annual stockpile destruction reports.",
        "limitation": "Self-reported data; no independent verification.",
    },
    {
        "tier": "Verified compliance",
        "treaty": "Chemical Weapons Convention",
        "year": "1993",
        "mechanism": "OPCW conducts routine and challenge inspections.",
        "limitation": "Intrusive oversight can be politically costly.",
    },
    {
        "tier": "Verified compliance",
        "treaty": "New START Treaty",
        "year": "2010",
        "mechanism": "Quota-based bilateral inspections plus telemetry.",
        "limitation": "Depends on sustained bilateral cooperation.",
    },
]

fig3, ax3 = plt.subplots(figsize=(13.5, 4.35), constrained_layout=True)
ax3.axis("off")

col_labels = [
    "Compliance tier",
    "Treaty example",
    "Year",
    "Mechanism",
    "Key limitation",
]
cell_text = [
    [
        row["tier"],
        row["treaty"],
        row["year"],
        row["mechanism"],
        row["limitation"],
    ]
    for row in EXAMPLES
]

col_widths = [0.18, 0.22, 0.08, 0.27, 0.25]
table = ax3.table(
    cellText=cell_text,
    colLabels=col_labels,
    colWidths=col_widths,
    cellLoc="left",
    colLoc="left",
    bbox=[0.0, 0.10, 1.0, 0.84],
)
table.auto_set_font_size(False)
table.set_fontsize(8.9)
table.scale(1, 1.95)

for (r, c), cell in table.get_celld().items():
    cell.set_edgecolor(PALETTE["light_gray"])
    cell.set_linewidth(1.0)
    if r == 0:
        cell.set_facecolor(PALETTE["navy"])
        cell.set_text_props(color="white", fontweight="bold", va="center")
    else:
        row = EXAMPLES[r - 1]
        if c == 0:
            tier = row["tier"]
            cell.set_facecolor(TIER_COLORS[tier])
            cell.set_text_props(
                color="white" if tier != "No mechanism" else "#4A5568",
                fontweight="bold",
                va="center",
            )
        else:
            cell.set_facecolor("white" if r % 2 else PALETTE["offwhite"])
            if c == 4:
                cell.set_text_props(color=PALETTE["red"], va="center")
            elif c == 1:
                cell.set_text_props(color=PALETTE["navy"], fontweight="bold", va="center")
            elif c == 2:
                cell.set_text_props(color=PALETTE["mid_gray"], va="center")
            else:
                cell.set_text_props(color=PALETTE["navy"], va="center")

ax3.set_title(
    "Compliance Tiers in Practice: Treaty Examples",
    fontsize=13,
    fontweight="bold",
    color=PALETTE["navy"],
    pad=1,
    loc="center",
)

fig3.savefig(FIG_DIR / "fig3_treaty_examples.png", dpi=160,
             bbox_inches="tight", facecolor="white")
plt.close(fig3)
print("Saved: fig3_treaty_examples.png")

# =============================================================================
# FIGURE 4  ── Risk × Compliance framework with AI analogue column
# =============================================================================
MATRIX = [
    {
        "risk_level": "High",
        "weapon_domain": "Nuclear strategic systems\nICBMs, SLBMs, CW/BW",
        "observed_compliance": "Verified compliance\nmean ~3.0",
        "ai_governance_analogue": "Independent audits,\nred-team evaluations,\ncompute monitoring",
        "risk_color": PALETTE["red"],
    },
    {
        "risk_level": "Medium",
        "weapon_domain": "Conventional weapons\nland, air, sea",
        "observed_compliance": "Demonstrated compliance\nmean ~1.3-1.7",
        "ai_governance_analogue": "Model cards,\nsafety cases,\nincident reporting",
        "risk_color": "#E9803A",
    },
    {
        "risk_level": "Low",
        "weapon_domain": "General treaties\nearly agreements",
        "observed_compliance": "Consultation or none\nmean <1.0",
        "ai_governance_analogue": "Voluntary commitments,\nindustry self-regulation",
        "risk_color": PALETTE["teal"],
    },
]

fig4, ax4 = plt.subplots(figsize=(12.5, 4.2), constrained_layout=True)
ax4.axis("off")

col_labels = [
    "Risk level",
    "Weapon domain",
    "Observed compliance\n(arms control)",
    "AI governance analogue",
]
cell_text = [
    [
        row["risk_level"],
        row["weapon_domain"],
        row["observed_compliance"],
        row["ai_governance_analogue"],
    ]
    for row in MATRIX
]

col_widths = [0.12, 0.24, 0.24, 0.40]
table = ax4.table(
    cellText=cell_text,
    colLabels=col_labels,
    colWidths=col_widths,
    cellLoc="left",
    colLoc="left",
    bbox=[0.0, 0.10, 1.0, 0.82],
)
table.auto_set_font_size(False)
table.set_fontsize(9.2)
table.scale(1, 2.15)

for (r, c), cell in table.get_celld().items():
    cell.set_edgecolor(PALETTE["light_gray"])
    cell.set_linewidth(1.0)
    if r == 0:
        cell.set_facecolor(PALETTE["navy"])
        cell.set_text_props(color="white", fontweight="bold", va="center")
    else:
        row = MATRIX[r - 1]
        if c == 0:
            cell.set_facecolor(row["risk_color"])
            cell.set_text_props(color="white", fontweight="bold", va="center")
        else:
            cell.set_facecolor("white")
            cell.set_text_props(color=PALETTE["navy"], va="center")

ax4.set_title(
    "Risk and Compliance: Simple Arms-Control-to-AI Mapping",
    fontsize=13,
    fontweight="bold",
    color=PALETTE["navy"],
    pad=1,
    loc="center",
)

fig4.savefig(FIG_DIR / "fig4_risk_compliance_framework.png",
             dpi=160,
             bbox_inches="tight", facecolor="white")
plt.close(fig4)
print("Saved: fig4_risk_compliance_framework.png")

# =============================================================================
# FIGURE 4B ── Empirical grouping × observed compliance shares
# =============================================================================
group_df = (
    info[["agreement_id", "compliance_label"]]
    .merge(agreement_group, on="agreement_id", how="left")
    .assign(empirical_group=lambda df: df["empirical_group"].fillna("General / unclassified agreements"))
)
group_counts = (
    group_df.groupby(["empirical_group", "compliance_label"])["agreement_id"]
    .nunique()
    .unstack(fill_value=0)
    .reindex([
        "High-compliance weapon domains",
        "Medium-compliance weapon domains",
        "General / unclassified agreements",
    ])
)
for lbl in TIER_ORDER:
    if lbl not in group_counts.columns:
        group_counts[lbl] = 0
group_counts = group_counts[TIER_ORDER]
group_shares = group_counts.div(group_counts.sum(axis=1), axis=0).fillna(0)

group_labels = [
    f"High-compliance weapon domains (n={int(group_counts.loc['High-compliance weapon domains'].sum())})",
    f"Medium-compliance weapon domains (n={int(group_counts.loc['Medium-compliance weapon domains'].sum())})",
    f"General / unclassified agreements (n={int(group_counts.loc['General / unclassified agreements'].sum())})",
]

fig4b, ax4b = plt.subplots(figsize=(12.5, 5.0), constrained_layout=True)
ax4b.set_facecolor("white")
y_pos = np.arange(len(group_shares.index))
left = np.zeros(len(group_shares.index))

for lbl in TIER_ORDER:
    vals = group_shares[lbl].values
    ax4b.barh(
        y_pos,
        vals,
        left=left,
        color=TIER_COLORS[lbl],
        height=0.6,
        edgecolor="white",
        linewidth=1.1,
        label=lbl,
    )
    for i, (v, lft) in enumerate(zip(vals, left)):
        if v >= 0.09:
            ax4b.text(
                lft + v / 2,
                i,
                f"{v:.0%}",
                ha="center",
                va="center",
                fontsize=8.5,
                fontweight="bold",
                color="white" if lbl != "No mechanism" else "#4A5568",
            )
    left += vals

ax4b.set_xlim(0, 1)
ax4b.set_xticks(np.linspace(0, 1, 6))
ax4b.set_xticklabels([f"{x:.0%}" for x in np.linspace(0, 1, 6)])
ax4b.set_yticks(y_pos)
ax4b.set_yticklabels(group_labels, fontsize=9.5, color=PALETTE["navy"])
ax4b.invert_yaxis()
ax4b.set_xlabel("Share of agreements in each compliance tier", fontsize=10)
ax4b.set_title(
    "Compliance Tiers by Empirical Group",
    fontsize=13,
    fontweight="bold",
    color=PALETTE["navy"],
    pad=8,
    loc="left",
)
ax4b.axvline(0.5, color=PALETTE["light_gray"], lw=1, ls="--", zorder=0)
ax4b.grid(axis="x", color=PALETTE["light_gray"], lw=0.6, alpha=0.6)
ax4b.spines[["top", "right"]].set_visible(False)
ax4b.spines[["left", "bottom"]].set_color(PALETTE["light_gray"])
ax4b.legend(
    ncol=2,
    loc="lower center",
    bbox_to_anchor=(0.5, 1.02),
    frameon=False,
    fontsize=8.5,
    columnspacing=1.2,
    handletextpad=0.5,
)
fig4b.savefig(FIG_DIR / "fig4b_empirical_risk_groups.png", dpi=160,
              bbox_inches="tight", facecolor="white")
plt.close(fig4b)
print("Saved: fig4b_empirical_risk_groups.png")

# =============================================================================
# Console summary
# =============================================================================
print("\n=== KEY METRICS ===")
dist = info["compliance_label"].value_counts()
for lbl, n in dist.items():
    print(f"  {lbl:<30} {n:>3} ({n/len(info):.0%})")
print()
print("Mean compliance score by weapon category:")
print(score_by_cat.to_string())
print()
print(f"No compliance mechanism: {(info['compliance_label']=='No mechanism').sum()/len(info):.0%}")
print("Empirical group compliance shares:")
print((group_shares * 100).round(1).astype(str).add("%").to_string())
print("All figures saved to:", FIG_DIR)
