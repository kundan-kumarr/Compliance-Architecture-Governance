"""
Challenge 8 — LLM Treaty Text Classification
AMC Research Sprint | April 2026

Research question:
  Given only treaty name, weapon category, and extracted definitions — no compliance
  labels — does a language model recover the same compliance tiers AMC researchers
  coded manually?

The accuracy number is secondary. The research value is in the disagreements:

  POLICY GAP      (LLM > actual): Treaty name/category signals strong verification
                  intent, but AMC coding shows no operational mechanism. Highlights
                  where design intent outran implementation (e.g. BWC).

  HIDDEN COMPLIANCE (LLM < actual): Verified compliance exists but is not legible
                  from treaty name alone. Highlights where domain knowledge adds
                  value beyond surface text.

Outputs:
  figures/llm_classification_comparison.png   — confusion matrix + disagreement panel
  llm_classification_results.csv              — full per-agreement results

Setup:
  Copy .env.example → .env and fill in one key:
    ANTHROPIC_API_KEY=sk-ant-...   (Claude Haiku,  ~$0.05 / run)
    OPENAI_API_KEY=sk-...          (GPT-4o-mini,   ~$0.04 / run)
"""

import os
import json
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def _load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE lines without requiring python-dotenv."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and value not in {"sk-ant-...", "sk-..."}:
            os.environ[key] = value

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(ROOT / ".env", override=True)
    load_dotenv(ROOT / ".env.example", override=True)
except ImportError:
    _load_env_file(ROOT / ".env")
    _load_env_file(ROOT / ".env.example")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIG_DIR  = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(exist_ok=True)
OUT_CSV  = Path(__file__).resolve().parent / "llm_classification_results.csv"

# ── Provider selection (before any LLM calls) ─────────────────────────────────
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")
OPENAI_KEY    = os.environ.get("OPENAI_API_KEY")

if ANTHROPIC_KEY:
    import anthropic  # type: ignore
    _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    PROVIDER = "anthropic"
    print("Provider: Anthropic (claude-haiku-4-5)")
elif OPENAI_KEY:
    import openai  # type: ignore
    _openai_client = openai.OpenAI(api_key=OPENAI_KEY)
    PROVIDER = "openai"
    print("Provider: OpenAI (gpt-4o-mini)")
else:
    raise SystemExit(
        "ERROR: No API key found.\n"
        "Add ANTHROPIC_API_KEY or OPENAI_API_KEY to your .env file.\n"
        "See .env.example for the format."
    )


def _call_llm(user: str) -> str:
    """Unified LLM call — returns raw text response."""
    system = (
        "You are an expert in international arms control law. "
        "Respond with valid JSON only. No explanation outside the JSON object."
    )
    if PROVIDER == "anthropic":
        resp = _anthropic_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text.strip()
    else:
        resp = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=120,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
        return resp.choices[0].message.content.strip()


# ── Load data ─────────────────────────────────────────────────────────────────
info    = pd.read_csv(DATA_DIR / "amcdata_agreement_info_V2.csv",     encoding="latin1")
weapons = pd.read_csv(DATA_DIR / "amcdata_weapons_facilities_V2.csv", encoding="latin1")

# ── Actual compliance scores ──────────────────────────────────────────────────
def compliance_level(row):
    if row.get("verified_compliance_mechanism", 0) == 1:     return 3
    if row.get("demonstrated_compliance_mechanism", 0) == 1: return 2
    if row.get("consultation_mechanism", 0) == 1:             return 1
    return 0

info["compliance_score"] = info.apply(compliance_level, axis=1)
TIER_LABELS = {0: "None", 1: "Consultation", 2: "Demonstrated", 3: "Verified"}
info["compliance_label"] = info["compliance_score"].map(TIER_LABELS)

# ── Weapon broad category per agreement ───────────────────────────────────────
summary_rows = (
    weapons[weapons["item"].str.contains("Summary Category", na=False)]
    [["agreement_id", "item"]].drop_duplicates()
)
summary_rows["weapon_cat"] = summary_rows["item"].str.extract(r"\((.+)\)")

def broad_cat(cat):
    if pd.isna(cat):                                             return "General / Unknown"
    if "Nuclear" in cat:                                         return "Nuclear Weapons"
    if "Biological" in cat or "Chemical" in cat:                 return "Biological / Chemical Weapons"
    if any(x in cat for x in ["ICBM","SLBM","Bomber","Submarine"]): return "Strategic Delivery Systems"
    return "Conventional Weapons"

summary_rows["weapon_broad"] = summary_rows["weapon_cat"].apply(broad_cat)
cat_per_agreement = (
    summary_rows.groupby("agreement_id")["weapon_broad"]
    .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else "General / Unknown")
    .reset_index()
)

# ── Weapon definitions per agreement ──────────────────────────────────────────
wid = (
    weapons[
        weapons["weapon_item_definition"].notna() &
        (weapons["weapon_item_definition"].astype(str).str.strip() != "99")
    ]
    .groupby("agreement_id")["weapon_item_definition"]
    .apply(lambda x: " | ".join(x.astype(str).str.strip().unique()))
    .reset_index(name="weapon_definition")
)

# ── Build context table ───────────────────────────────────────────────────────
context_df = (
    info[["agreement_id", "year", "title_full", "title_short"]]
    .merge(cat_per_agreement, on="agreement_id", how="left")
    .merge(wid,               on="agreement_id", how="left")
)
context_df["weapon_broad"] = context_df["weapon_broad"].fillna("General / Unknown")

# ── Classification function ───────────────────────────────────────────────────
PROMPT_TEMPLATE = """\
Given treaty: {title}
Year: {year}
Weapon category: {weapon_broad}
Weapon definition: {weapon_def}

Classify the most likely compliance oversight mechanism based on what treaties in
this domain typically include:

  0 = None          — no compliance monitoring; relies on political goodwill
  1 = Consultation  — periodic review meetings; no binding reporting or inspection
  2 = Demonstrated  — states self-report compliance (declarations, notifications)
  3 = Verified      — independent third parties actively inspect or verify

Respond with JSON only:
{{"score": <0|1|2|3>, "confidence": <"high"|"medium"|"low">, "reasoning": "<one sentence>"}}"""


def classify_agreement(row):
    defn = str(row["weapon_definition"])[:600] if pd.notna(row.get("weapon_definition")) else "Not available"
    prompt = PROMPT_TEMPLATE.format(
        title=row["title_full"],
        year=int(row["year"]),
        weapon_broad=row["weapon_broad"],
        weapon_def=defn,
    )
    try:
        raw = _call_llm(prompt)
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        return int(parsed["score"]), parsed.get("confidence", "medium"), parsed.get("reasoning", "")
    except Exception as e:
        return -1, "error", str(e)


# ── Run / load cache ──────────────────────────────────────────────────────────
def run_classification() -> pd.DataFrame:
    print(f"Classifying {len(context_df)} agreements...")
    records = []
    for idx, (_, row) in enumerate(context_df.iterrows()):
        actual = info.loc[info["agreement_id"] == row["agreement_id"],
                          "compliance_score"].values[0]
        score, conf, reason = classify_agreement(row)
        records.append({
            "agreement_id":   row["agreement_id"],
            "title_short":    row["title_short"],
            "year":           int(row["year"]),
            "weapon_broad":   row["weapon_broad"],
            "actual_score":   int(actual),
            "llm_score":      score,
            "llm_confidence": conf,
            "llm_reasoning":  reason,
        })
        if (idx + 1) % 20 == 0:
            print(f"  {idx+1}/{len(context_df)} done...")
            time.sleep(1)

    classified = pd.DataFrame(records)
    classified.to_csv(OUT_CSV, index=False)
    print(f"Saved: {OUT_CSV.name}")
    return classified

if OUT_CSV.exists():
    print(f"Loading cached results from {OUT_CSV.name}")
    results_df = pd.read_csv(OUT_CSV)
    valid_cached = results_df[results_df["llm_score"] >= 0] if "llm_score" in results_df else pd.DataFrame()
    if valid_cached.empty:
        print("Cached results have no valid LLM scores; regenerating...")
        results_df = run_classification()
else:
    results_df = run_classification()

# ── Post-process ──────────────────────────────────────────────────────────────
valid = results_df[results_df["llm_score"] >= 0].copy()
valid["actual_label"] = valid["actual_score"].map(TIER_LABELS)
valid["llm_label"]    = valid["llm_score"].map(TIER_LABELS)
valid["match"]        = valid["actual_score"] == valid["llm_score"]
valid["off_by"]       = valid["actual_score"] - valid["llm_score"]  # signed: + = LLM under, - = LLM over

# Disagreement type — the core finding
def disagree_type(row):
    if row["llm_score"] > row["actual_score"]: return "Policy gap\n(LLM higher)"
    if row["llm_score"] < row["actual_score"]: return "Hidden compliance\n(LLM lower)"
    return "Match"

valid["disagree_type"] = valid.apply(disagree_type, axis=1)

exact_acc  = valid["match"].mean()
within_one = (valid["off_by"].abs() <= 1).mean()
n_gap      = (valid["disagree_type"] == "Policy gap\n(LLM higher)").sum()
n_hidden   = (valid["disagree_type"] == "Hidden compliance\n(LLM lower)").sum()

print(f"\n=== LLM CLASSIFICATION RESULTS ===")
print(f"n={len(valid)}  exact={exact_acc:.0%}  within-one={within_one:.0%}")
print(f"Policy gaps (LLM>actual): {n_gap}   Hidden compliance (LLM<actual): {n_hidden}")

tiers_order = ["None", "Consultation", "Demonstrated", "Verified"]
conf_matrix = pd.crosstab(
    valid["actual_label"], valid["llm_label"],
    rownames=["Actual"], colnames=["LLM predicted"]
).reindex(index=tiers_order, columns=tiers_order, fill_value=0)
print("\nConfusion matrix:")
print(conf_matrix.to_string())

# ── Interesting disagreements ─────────────────────────────────────────────────
policy_gaps = (
    valid[valid["disagree_type"] == "Policy gap\n(LLM higher)"]
    [["title_short","year","weapon_broad","actual_label","llm_label","llm_confidence","llm_reasoning"]]
    .sort_values("year")
)
hidden_comp = (
    valid[valid["disagree_type"] == "Hidden compliance\n(LLM lower)"]
    [["title_short","year","weapon_broad","actual_label","llm_label","llm_confidence","llm_reasoning"]]
    .sort_values("year")
)

print(f"\nPOLICY GAPS — LLM expected verification, AMC coded none ({len(policy_gaps)}):")
print(policy_gaps[["title_short","year","actual_label","llm_label","llm_reasoning"]].to_string())
print(f"\nHIDDEN COMPLIANCE — AMC coded verification, LLM didn't expect it ({len(hidden_comp)}):")
print(hidden_comp[["title_short","year","actual_label","llm_label","llm_reasoning"]].to_string())

# =============================================================================
# FIGURE — 3 panels: confusion matrix | disagreement type bar | disagreement table
# =============================================================================
COLORS = {
    "None":           "#d9d9d9",
    "Consultation":   "#f4a460",
    "Demonstrated":   "#4a9bc7",
    "Verified":       "#1a5e7a",
}

fig = plt.figure(figsize=(16, 7))
gs  = fig.add_gridspec(1, 3, width_ratios=[1.1, 0.9, 1.7], wspace=0.35)
ax_cm, ax_bar, ax_tbl = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])

# ── Panel 1: Confusion matrix ─────────────────────────────────────────────────
mat      = conf_matrix.values.astype(float)
mat_norm = mat / (mat.sum(axis=1, keepdims=True) + 1e-9)
im = ax_cm.imshow(mat_norm, cmap="Blues", vmin=0, vmax=1, aspect="auto")
for i in range(len(tiers_order)):
    for j in range(len(tiers_order)):
        v = int(mat[i, j])
        ax_cm.text(j, i, str(v), ha="center", va="center", fontsize=11,
                   color="white" if mat_norm[i, j] > 0.5 else "#333", fontweight="bold")
        if i == j:
            ax_cm.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1,
                                           fill=False, edgecolor="#c0392b", lw=2))
ax_cm.set_xticks(range(len(tiers_order)))
ax_cm.set_yticks(range(len(tiers_order)))
ax_cm.set_xticklabels(tiers_order, rotation=30, ha="right", fontsize=9)
ax_cm.set_yticklabels(tiers_order, fontsize=9)
ax_cm.set_xlabel("LLM Predicted", fontsize=10)
ax_cm.set_ylabel("AMC Actual", fontsize=10)
ax_cm.set_title(f"Confusion Matrix\nExact {exact_acc:.0%} | Within-1 {within_one:.0%}",
                fontsize=11, fontweight="bold")

# ── Panel 2: Disagreement type bar ────────────────────────────────────────────
disagree_counts = valid["disagree_type"].value_counts()
bar_labels = ["Match", "Policy gap\n(LLM higher)", "Hidden compliance\n(LLM lower)"]
bar_vals   = [disagree_counts.get(l, 0) for l in bar_labels]
bar_colors = ["#1a5e7a", "#c0392b", "#e67e22"]
bars = ax_bar.barh(bar_labels, bar_vals, color=bar_colors, edgecolor="white", height=0.5)
for bar, val in zip(bars, bar_vals):
    ax_bar.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                str(int(val)), va="center", fontsize=10, fontweight="bold", color="#333")
ax_bar.set_xlabel("Number of agreements", fontsize=10)
ax_bar.set_title("Disagreement Types\n(the signal, not noise)", fontsize=11, fontweight="bold")
ax_bar.set_xlim(0, max(1, max(bar_vals)) * 1.25)
ax_bar.spines[["top", "right"]].set_visible(False)
ax_bar.tick_params(axis="y", labelsize=9)

# ── Panel 3: Top disagreements table ─────────────────────────────────────────
ax_tbl.axis("off")
# Show top 5 policy gaps + top 5 hidden compliance
top_gaps   = policy_gaps.head(5)[["title_short","year","actual_label","llm_label"]]
top_hidden = hidden_comp.head(5)[["title_short","year","actual_label","llm_label"]]

def draw_mini_table(ax, df, title, title_color, y_start, row_h=0.10):
    ax.text(0.01, y_start + row_h, title, transform=ax.transAxes,
            fontsize=9.5, fontweight="bold", color=title_color, va="bottom")
    ax.plot([0.01, 0.99], [y_start, y_start], color=title_color,
            linewidth=1.2, transform=ax.transAxes)
    cols = ["Treaty", "Year", "Actual", "LLM"]
    xs   = [0.01, 0.52, 0.68, 0.83]
    # Header
    for x, c in zip(xs, cols):
        ax.text(x, y_start - 0.01, c, transform=ax.transAxes,
                fontsize=8, fontweight="bold", color="#555", va="top")
    for r, (_, row) in enumerate(df.iterrows()):
        y = y_start - (r + 1.3) * row_h
        name = str(row["title_short"])[:28] + ("…" if len(str(row["title_short"])) > 28 else "")
        ax.text(xs[0], y, name,     transform=ax.transAxes, fontsize=7.5, va="center", color="#222")
        ax.text(xs[1], y, str(int(row["year"])), transform=ax.transAxes, fontsize=7.5, va="center", color="#555")
        ax.text(xs[2], y, row["actual_label"], transform=ax.transAxes, fontsize=7.5,
                va="center", color=COLORS.get(row["actual_label"], "#333"), fontweight="bold")
        ax.text(xs[3], y, row["llm_label"],    transform=ax.transAxes, fontsize=7.5,
                va="center", color=COLORS.get(row["llm_label"], "#333"), fontweight="bold")
    return y_start - (len(df) + 2.5) * row_h

next_y = draw_mini_table(ax_tbl, top_gaps,   "POLICY GAPS — LLM expected more oversight", "#c0392b", 0.96)
draw_mini_table(ax_tbl, top_hidden, "HIDDEN COMPLIANCE — Verification not legible from name", "#e67e22", next_y)
ax_tbl.set_title("Where LLM and AMC Disagree", fontsize=11, fontweight="bold", pad=8)

plt.suptitle("LLM Treaty Classification vs AMC Human Coding",
             fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
fig.savefig(FIG_DIR / "llm_classification_comparison.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("\nSaved: llm_classification_comparison.png")



