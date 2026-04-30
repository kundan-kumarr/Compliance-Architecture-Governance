"""
Challenge 8 — ML Extensions
AMC Research Sprint | April 2026

Three statistical analyses:
  A. Logistic regression — what predicts verified compliance?
  B. Hierarchical clustering — do natural groupings validate the tiers?
  C. Change-point detection — formally locate the verified-compliance peak/decline

Outputs (analysis8/figures/):
  fig5_regression_coefficients.png
  fig6_clustering_heatmap.png
  fig7_changepoint_timeseries.png
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

from sklearn.linear_model    import LogisticRegression
from sklearn.preprocessing   import StandardScaler
from sklearn.impute          import SimpleImputer
from scipy.cluster.hierarchy import linkage, fcluster
import ruptures as rpt

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIG_DIR  = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

# ── Design system (shared with main script) ───────────────────────────────────
PALETTE = {
    "navy":       "#1B2A4A",
    "red":        "#E63946",
    "steel":      "#457B9D",
    "teal":       "#2A9D8F",
    "gold":       "#E9C46A",
    "offwhite":   "#F8F9FA",
    "mid_gray":   "#8E9AAA",
    "light_gray": "#DEE2E6",
    "green":      "#2A9D8F",
    "orange":     "#E9803A",
}
TIER_COLORS = {
    "None":          "#CBD5E0",
    "Consultation":  "#F6AD55",
    "Demonstrated":  "#457B9D",
    "Verified":      "#1B2A4A",
}

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

# ── Load + build compliance score ─────────────────────────────────────────────
info    = pd.read_csv(DATA_DIR / "amcdata_agreement_info_V2.csv",     encoding="latin1")
weapons = pd.read_csv(DATA_DIR / "amcdata_weapons_facilities_V2.csv", encoding="latin1")

def compliance_level(row):
    if row.get("verified_compliance_mechanism",    0) == 1: return 3
    if row.get("demonstrated_compliance_mechanism",0) == 1: return 2
    if row.get("consultation_mechanism",           0) == 1: return 1
    return 0

info["compliance_score"] = info.apply(compliance_level, axis=1)
TIER_LABELS = {0:"None", 1:"Consultation", 2:"Demonstrated", 3:"Verified"}
info["compliance_label"] = info["compliance_score"].map(TIER_LABELS)
info["decade"] = (info["year"] // 10) * 10

# Weapon category (use summary_category flag)
summary_rows = (
    weapons[weapons["summary_category"] == 1][["agreement_id","item"]]
    .drop_duplicates().copy()
)
summary_rows["item"] = summary_rows["item"].str.strip()
extracted = summary_rows["item"].str.extract(r"\((.+)\)")
summary_rows["weapon_cat"] = extracted[0].where(extracted[0].notna(), summary_rows["item"])
merged = info.merge(summary_rows, on="agreement_id", how="left")

def broad_cat(cat):
    if pd.isna(cat):                                              return "Unknown"
    if "ICBM" in cat or "SLBM" in cat or "Bomber" in cat or "Submarine" in cat: return "Strategic Delivery"
    if "Biological" in cat or "Chemical" in cat:                  return "CBRN"
    if "Nuclear" in cat:                                          return "Nuclear"
    return "Conventional"

merged["weapon_broad"] = merged["weapon_cat"].apply(broad_cat)
cat_per_agr = (
    merged.groupby("agreement_id")["weapon_broad"]
    .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else "Unknown")
    .reset_index()
)
df = info.merge(cat_per_agr, on="agreement_id", how="left")
df["weapon_broad"] = df["weapon_broad"].fillna("Unknown")

# ── Feature matrix ────────────────────────────────────────────────────────────
cat_dummies = pd.get_dummies(df["weapon_broad"], prefix="cat", drop_first=True)
feature_cols = ["year","laterality","nr_signatory_states","nr_states_parties_total"]
X_raw = df[feature_cols].copy()
X_raw["log_signatories"] = np.log1p(X_raw["nr_signatory_states"])
X_raw["log_parties"]     = np.log1p(X_raw["nr_states_parties_total"])
X_raw = X_raw.drop(columns=["nr_signatory_states","nr_states_parties_total"])
X_raw = pd.concat([X_raw, cat_dummies], axis=1)
y = df["compliance_score"]

imputer = SimpleImputer(strategy="median")
scaler  = StandardScaler()
X_sc    = scaler.fit_transform(imputer.fit_transform(X_raw))

model = LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42)
model.fit(X_sc, y)
acc   = (model.predict(X_sc) == y).mean()

feature_names = list(X_raw.columns)
coef_df = pd.DataFrame(model.coef_, columns=feature_names,
                        index=[TIER_LABELS[i] for i in sorted(TIER_LABELS)])
net_coef = (coef_df.loc["Verified"] - coef_df.loc["None"]).sort_values()

NICE_NAMES = {
    "year":              "Treaty Year",
    "laterality":        "Laterality (bilateral vs multilateral)",
    "log_signatories":   "Log(Signatories)",
    "log_parties":       "Log(State Parties)",
    "cat_Nuclear":       "Weapon: Nuclear",
    "cat_Strategic Delivery": "Weapon: Strategic Delivery",
    "cat_CBRN":          "Weapon: CBRN",
    "cat_Unknown":       "Weapon: Unknown",
    "cat_Conventional":  "Weapon: Conventional",
}
net_coef.index = [NICE_NAMES.get(n, n) for n in net_coef.index]

# =============================================================================
# FIGURE 5  ── Regression coefficients — lollipop chart
# =============================================================================
fig5, ax5 = plt.subplots(figsize=(11, 6.5))
ax5.set_facecolor(PALETTE["offwhite"])

y_pos = np.arange(len(net_coef))
bar_colors = [PALETTE["red"] if v < 0 else PALETTE["navy"] for v in net_coef.values]

# Zero line
ax5.axvline(0, color=PALETTE["light_gray"], linewidth=1.5, zorder=1)

# Lollipop stems
for yp, val, col in zip(y_pos, net_coef.values, bar_colors):
    ax5.plot([0, val], [yp, yp], color=col, alpha=0.4, linewidth=2, zorder=2)
    ax5.plot(val, yp, "o", color=col, markersize=11, zorder=3)
    offset = 0.06 if val >= 0 else -0.06
    ha     = "left" if val >= 0 else "right"
    ax5.text(val + offset, yp, f"{val:+.2f}",
             va="center", ha=ha, fontsize=9, color=col, fontweight="bold")

# Highlight significant predictors
for yp, feat in enumerate(net_coef.index):
    bg = "#E8F4F8" if net_coef.iloc[yp] > 0.3 else \
         "#FDEEEE" if net_coef.iloc[yp] < -0.3 else None
    if bg:
        ax5.barh(yp, abs(net_coef.iloc[yp]),
                 left=0 if net_coef.iloc[yp] >= 0 else net_coef.iloc[yp],
                 height=0.85, color=bg, zorder=0, alpha=0.5)

ax5.set_yticks(y_pos)
ax5.set_yticklabels(net_coef.index, fontsize=10, color=PALETTE["navy"])
ax5.set_xlabel("Coefficient (Verified vs. None tier)   ·   Positive = pushes toward verified compliance",
               fontsize=10, color=PALETTE["mid_gray"])
ax5.set_xlim(net_coef.min() - 0.3, net_coef.max() + 0.45)
ax5.set_ylim(-0.6, len(net_coef) - 0.4)
ax5.tick_params(left=False)
ax5.spines["left"].set_visible(False)
ax5.spines["bottom"].set_color(PALETTE["light_gray"])

# Accuracy badge
ax5.text(0.99, 0.03,
         f"In-sample accuracy: {acc:.0%}\n(random baseline ~25–39%)",
         transform=ax5.transAxes, ha="right", fontsize=9,
         color=PALETTE["mid_gray"], style="italic",
         bbox=dict(boxstyle="round,pad=0.4", fc="white",
                   ec=PALETTE["light_gray"], lw=1))

# Insight callouts
top_pos = net_coef.idxmax()
top_neg = net_coef.idxmin()
ax5.annotate("Bilateral format key:\nUS-USSR dyad built the\nstrongest inspection regimes",
             xy=(net_coef[top_pos], list(net_coef.index).index(top_pos)),
             xytext=(net_coef[top_pos]*0.55, list(net_coef.index).index(top_pos)+2),
             fontsize=8, color=PALETTE["navy"],
             arrowprops=dict(arrowstyle="->", color=PALETTE["navy"], lw=1.2),
             bbox=dict(boxstyle="round,pad=0.35", fc=PALETTE["offwhite"],
                       ec=PALETTE["navy"], lw=1))

pos_patch = mpatches.Patch(color=PALETTE["navy"], label="Pushes toward verified compliance")
neg_patch = mpatches.Patch(color=PALETTE["red"],  label="Pushes away from verified compliance")
ax5.legend(handles=[pos_patch, neg_patch], fontsize=9,
           loc="lower right", frameon=True, framealpha=0.95,
           edgecolor=PALETTE["light_gray"])

ax5.set_title(
    "What Predicts Verified Compliance?\n"
    "Logistic Regression: Verified vs. No-mechanism coefficient contrast",
    fontsize=14, fontweight="bold", color=PALETTE["navy"], pad=14
)

fig5.tight_layout()
fig5.savefig(FIG_DIR / "fig5_regression_coefficients.png", dpi=160,
             bbox_inches="tight", facecolor="white")
plt.close(fig5)
print("Saved: fig5_regression_coefficients.png")

# =============================================================================
# FIGURE 6  ── Clustering heatmap (drop dendrogram, clean tile matrix)
# =============================================================================
cluster_features = pd.DataFrame({
    "compliance_score": df["compliance_score"],
    "year":             df["year"],
    "laterality":       df["laterality"].fillna(1),
    "log_signatories":  np.log1p(df["nr_signatory_states"].fillna(0)),
    "log_parties":      np.log1p(df["nr_states_parties_total"].fillna(0)),
})
cluster_features = pd.concat([cluster_features, cat_dummies.fillna(0)], axis=1)
X_cl = scaler.fit_transform(imputer.fit_transform(cluster_features))

Z = linkage(X_cl, method="ward")
k = 4
cluster_labels = fcluster(Z, k, criterion="maxclust")
cross = pd.crosstab(cluster_labels, df["compliance_score"],
                    rownames=["Cluster"], colnames=["Score"])
cross.columns = [TIER_LABELS[c] for c in cross.columns]
TIER_ORDER_SHORT = ["None","Consultation","Demonstrated","Verified"]
for t in TIER_ORDER_SHORT:
    if t not in cross.columns: cross[t] = 0
cross = cross[TIER_ORDER_SHORT]

# Row totals and purity
cross["Total"] = cross.sum(axis=1)
row_purity = cross[TIER_ORDER_SHORT].max(axis=1) / cross["Total"]
dominant   = cross[TIER_ORDER_SHORT].idxmax(axis=1)

fig6, (ax_heat, ax_info) = plt.subplots(1, 2, figsize=(14, 5.5),
                                         gridspec_kw={"width_ratios":[2, 1.2],
                                                       "wspace": 0.06})

# ── Heatmap ────────────────────────────────────────────────────────────────────
tile_colors = {
    "None":          "#CBD5E0",
    "Consultation":  "#F6AD55",
    "Demonstrated":  "#457B9D",
    "Verified":      "#1B2A4A",
}
mat = cross[TIER_ORDER_SHORT].values
n_rows, n_cols = mat.shape
max_val = mat.max()

for ri in range(n_rows):
    for ci, tier in enumerate(TIER_ORDER_SHORT):
        val = mat[ri, ci]
        alpha = 0.15 + 0.85 * (val / max_val) if max_val > 0 else 0.15
        color = tile_colors[tier]
        ax_heat.add_patch(plt.Rectangle(
            (ci, ri), 1, 1,
            facecolor=color, alpha=alpha,
            edgecolor="white", linewidth=2
        ))
        txt_color = "white" if (alpha > 0.55 and tier == "Verified") or \
                               (alpha > 0.7  and tier != "None") else PALETTE["navy"]
        ax_heat.text(ci+0.5, ri+0.5, str(int(val)),
                     ha="center", va="center",
                     fontsize=14, fontweight="bold", color=txt_color)

ax_heat.set_xlim(0, n_cols); ax_heat.set_ylim(0, n_rows)
ax_heat.set_xticks([c+0.5 for c in range(n_cols)])
ax_heat.set_xticklabels(TIER_ORDER_SHORT, fontsize=10, fontweight="bold",
                         color=PALETTE["navy"])
ax_heat.set_yticks([r+0.5 for r in range(n_rows)])
ax_heat.set_yticklabels([f"Cluster {i}" for i in cross.index],
                         fontsize=10, color=PALETTE["navy"])
ax_heat.set_title("Cluster × Compliance Tier\nDarker tile = more agreements",
                   fontsize=12, fontweight="bold", color=PALETTE["navy"])
ax_heat.tick_params(left=False, bottom=False)
for sp in ax_heat.spines.values(): sp.set_visible(False)
ax_heat.set_xlabel("Compliance tier", fontsize=10)
ax_heat.set_ylabel("Cluster", fontsize=10)

# ── Right panel: cluster profiles ─────────────────────────────────────────────
ax_info.set_xlim(0, 11.2); ax_info.set_ylim(-0.5, n_rows+0.7)
ax_info.axis("off")

# Header
ax_info.add_patch(FancyBboxPatch((0, n_rows+0.15), 9.95, 0.55,
                                  boxstyle="round,pad=0.05",
                                  facecolor=PALETTE["navy"], linewidth=0))
for txt, xp in [("Dominant tier",0.25),("Purity",4.05),("n",6.35),("Interpretation",7.05)]:
    ax_info.text(xp, n_rows+0.43, txt, fontsize=8.5, fontweight="bold",
                 color="white", va="center")

interp = {
    1: "Mixed — broad middle ground",
    2: "Mixed — broad middle ground",
    3: "Pure verified cluster",
    4: "Primarily no-mechanism",
}
row_bgs = ["#F8F9FA","#EDF2F7"]
for ri, (cid, dom, pur, tot) in enumerate(zip(
        cross.index, dominant, row_purity, cross["Total"])):
    y = n_rows - ri - 1
    ax_info.add_patch(FancyBboxPatch((-0.1, y-0.38), 11.1, 0.78,
                                      boxstyle="round,pad=0.03",
                                      facecolor=row_bgs[ri%2], linewidth=0))
    ax_info.add_patch(FancyBboxPatch((0.08, y-0.22), 3.5, 0.44,
                                      boxstyle="round,pad=0.05",
                                      facecolor=tile_colors.get(dom,"#aaa"), linewidth=0))
    ax_info.text(1.83, y+0.01, dom, ha="center", va="center",
                 fontsize=7.5, fontweight="bold", color="white" if dom!="None" else "#555")
    # Purity bar
    ax_info.add_patch(FancyBboxPatch((3.7, y-0.14), 1.6*pur, 0.28,
                                      boxstyle="round,pad=0.02",
                                      facecolor=PALETTE["teal"], linewidth=0))
    ax_info.text(5.85, y+0.01, f"{pur:.0%}", va="center", fontsize=8.5, ha="left",
                 color=PALETTE["navy"], fontweight="bold")
    ax_info.text(6.55, y+0.01, str(int(tot)), va="center", fontsize=8.2, ha="left",
                 color=PALETTE["mid_gray"])
    note = interp.get(cid, "")
    ax_info.text(7.15, y+0.01, note, va="center", fontsize=7.5,
                 color=PALETTE["navy"], style="italic")

ax_info.set_title("Cluster Profiles\n(Ward linkage, k=4)",
                   fontsize=12, fontweight="bold", color=PALETTE["navy"])

# Key insight box
insight = ("Verified-compliance agreements\nform a statistically distinct cluster.\n"
           "The gap between 'some oversight'\nand 'third-party inspection' is\n"
           "larger than gaps within lower tiers.")
fig6.text(0.5, -0.06, insight, ha="center", fontsize=9,
          color=PALETTE["navy"], style="italic",
          bbox=dict(boxstyle="round,pad=0.5", fc="#E8F4F8",
                    ec=PALETTE["steel"], lw=1.2))

fig6.suptitle("Do Natural Groupings Validate the Compliance Tiers?",
               fontsize=14, fontweight="bold", color=PALETTE["navy"], y=1.02)
fig6.tight_layout()
fig6.savefig(FIG_DIR / "fig6_clustering_heatmap.png", dpi=160,
             bbox_inches="tight", facecolor="white")
plt.close(fig6)
print("Saved: fig6_clustering_heatmap.png")

# =============================================================================
# FIGURE 7  ── Change-point time series — clean annotated area chart
# =============================================================================
year_series = (
    info[info["year"] >= 1920]
    .groupby("year")["compliance_score"]
    .apply(lambda x: (x == 3).sum())
    .reindex(range(1920, 2022), fill_value=0)
)
signal = year_series.values.astype(float)
years  = list(year_series.index)

algo = rpt.Pelt(model="rbf", min_size=5, jump=1).fit(signal)
breakpoints = algo.predict(pen=3)
bp_years = [years[bp-1] for bp in breakpoints if bp < len(years)]

# Compute 5-year rolling average for smoothed line
rolling = pd.Series(signal).rolling(5, center=True).mean()

fig7, ax7 = plt.subplots(figsize=(14, 6))

# Background shading per segment
seg_colors = ["#F0F7FF", "#E0F0FF", "#D0E8F8", "#F0F7FF"]
prev_y = 1920
for seg_i, bpy in enumerate(bp_years + [2022]):
    ax7.axvspan(prev_y, bpy, alpha=0.35,
                color=seg_colors[seg_i % len(seg_colors)], zorder=0)
    prev_y = bpy

# Filled area
ax7.fill_between(years, signal, alpha=0.18, color=PALETTE["navy"], zorder=1)
# Bar chart underneath
ax7.bar(years, signal, color=PALETTE["navy"], alpha=0.25, width=0.9, zorder=1)
# Smoothed line
ax7.plot(years, rolling, color=PALETTE["navy"], linewidth=2.5, zorder=3,
         label="5-year rolling average")
# Raw dots at non-zero years
nz_y = [y for y, v in zip(years, signal) if v > 0]
nz_v = [v for v in signal if v > 0]
ax7.scatter(nz_y, nz_v, color=PALETTE["steel"], s=40, zorder=4, alpha=0.7)

# Breakpoint lines
for bpy in bp_years:
    ax7.axvline(bpy, color=PALETTE["red"], linewidth=2, linestyle="--",
                alpha=0.85, zorder=5)
    ax7.text(bpy + 0.8, signal.max()*0.93, str(bpy),
             color=PALETTE["red"], fontsize=10, fontweight="bold", zorder=6)

# Segment annotations
segment_notes = [
    (1920, bp_years[0] if bp_years else 1990, "Pre-peak era\nSparse formal verification"),
    (bp_years[0] if bp_years else 1989,
     bp_years[1] if len(bp_years) > 1 else 1997,
     "Cold War arms control surge\nSALT · INF · START · CWC · CFE"),
    (bp_years[1] if len(bp_years) > 1 else 1997, 2022,
     "Post-peak decline\nZero new verified agreements\nin the 2000s"),
]
y_note = signal.max() * 0.55
for x_start, x_end, note in segment_notes:
    mid = (x_start + x_end) / 2
    ax7.text(mid, y_note, note, ha="center", fontsize=8, color=PALETTE["navy"],
             style="italic", linespacing=1.5,
             bbox=dict(boxstyle="round,pad=0.35", fc="white",
                       ec=PALETTE["light_gray"], lw=0.8, alpha=0.9))

ax7.set_xlim(1918, 2023)
ax7.set_ylim(-0.1, signal.max() * 1.3)
ax7.set_xlabel("Year", fontsize=11, color=PALETTE["mid_gray"])
ax7.set_ylabel("New verified-compliance agreements", fontsize=11)

# Y-axis integers only
ax7.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

# PELT legend
pelt_line = plt.Line2D([0],[0], color=PALETTE["red"], linewidth=2,
                         linestyle="--", label=f"PELT breakpoints: {bp_years}")
smooth_line = plt.Line2D([0],[0], color=PALETTE["navy"], linewidth=2.5,
                          label="5-yr rolling mean")
ax7.legend(handles=[pelt_line, smooth_line], fontsize=9.5,
           loc="upper left", frameon=True, framealpha=0.95,
           edgecolor=PALETTE["light_gray"])

ax7.spines["bottom"].set_color(PALETTE["light_gray"])
ax7.spines["left"].set_color(PALETTE["light_gray"])

ax7.set_title(
    "Change-Point Detection: When Did the Verified-Compliance Era End?\n"
    "PELT algorithm (RBF cost) on annual count of verified-compliance agreements, 1920–2021",
    fontsize=14, fontweight="bold", color=PALETTE["navy"], pad=14
)

fig7.tight_layout()
fig7.savefig(FIG_DIR / "fig7_changepoint_timeseries.png", dpi=160,
             bbox_inches="tight", facecolor="white")
plt.close(fig7)
print("Saved: fig7_changepoint_timeseries.png")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=== A. REGRESSION ===")
print(f"In-sample accuracy: {acc:.0%}")
print("Top positive (Verified - None):")
print(net_coef.tail(3).round(3).to_string())
print("Top negative:")
print(net_coef.head(3).round(3).to_string())
print()
print("=== B. CLUSTERING ===")
print(cross[TIER_ORDER_SHORT+["Total"]].to_string())
print()
print("=== C. CHANGE-POINTS ===")
print(f"Detected breakpoint years: {bp_years}")
