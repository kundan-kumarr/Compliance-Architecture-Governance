"""
Challenge 8 extension: AI oversight-gap case coding

This script does NOT infer autonomous-weapon or biosecurity findings from the AMC dataset.
Instead, it performs a small hand-coded comparative analysis using the AMC compliance tiers
as an explicit rubric for selected recent AI-governance cases.

Coding rubric for observed oversight tier:
  0 = No structured mechanism
  1 = Consultation / political dialogue / non-binding declaration
  2 = Structured reporting, evaluations, documentation, or internal monitoring
      but no standing independent verification with access rights
  3 = Independent external verification / inspection / challenge-access style oversight

Expected tier is assigned from the logic established in Challenge 8:
catastrophic, hard-to-observe, or fast-escalation domains should trend toward tier 3.

Outputs:
  - analysis8/ai_oversight_gap_cases.csv
  - analysis8/figures/fig8_ai_oversight_gap_cases.png
  - analysis8/challenge08_ai_oversight_gap.md
"""

from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = Path(__file__).resolve().parent
FIG_DIR = ANALYSIS_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)

PALETTE = {
    "navy": "#1B2A4A",
    "red": "#E63946",
    "steel": "#457B9D",
    "teal": "#2A9D8F",
    "gold": "#E9C46A",
    "light": "#DEE2E6",
    "dark": "#33415C",
    "soft": "#F8F9FA",
}

def write_with_lock_fallback(df: pd.DataFrame, path: Path) -> Path:
    """Write CSV output, falling back to a sibling file if the target is locked."""
    try:
        df.to_csv(path, index=False)
        return path
    except PermissionError:
        fallback = path.with_name(f"{path.stem}.updated{path.suffix}")
        df.to_csv(fallback, index=False)
        return fallback


def write_text_with_lock_fallback(path: Path, content: str) -> Path:
    """Write text output, falling back to a sibling file if the target is locked."""
    try:
        path.write_text(content, encoding="utf-8")
        return path
    except PermissionError:
        fallback = path.with_name(f"{path.stem}.updated{path.suffix}")
        fallback.write_text(content, encoding="utf-8")
        return fallback


plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

cases = [
    {
        "case": "UN process on autonomous weapons",
        "domain": "Autonomous weapons",
        "instrument_year": 2024,
        "case_type": "Recent AI-linked case",
        "expected_tier": 3,
        "observed_tier": 1,
        "source_title": "UNGA Resolution 78/241 and UN Secretary-General report A/79/88",
        "source_url": "https://digitallibrary.un.org/record/4033027?ln=en&v=pdf ; https://digitallibrary.un.org/record/4059475/files/A_79_88-EN.pdf",
        "why_expected": "Autonomous weapons combine escalation risk, targeting opacity, and potentially irreversible harm.",
        "why_observed": "Current governance is primarily multilateral consultation and norm-building, without binding verification or inspection rights.",
        "source_summary": "UNGA Resolution 78/241 requests views from states and stakeholders on lethal autonomous weapons systems and asks the Secretary-General to prepare a report. The Secretary-General report A/79/88 synthesizes those submissions and outlines regulatory options, but it does not establish an inspection, audit, or binding compliance regime.",
        "mapping_validation": "Observed tier 1 is appropriate because the cited UN documents create consultation, agenda-setting, and reporting processes rather than independent verification or challenge-access oversight.",
    },
    {
        "case": "AI-biosecurity preparedness",
        "domain": "AI-biosecurity / dual use biology",
        "instrument_year": 2025,
        "case_type": "Recent AI-linked case",
        "expected_tier": 3,
        "observed_tier": 2,
        "source_title": "OpenAI biology preparedness + International AI Safety Report",
        "source_url": "https://openai.com/index/preparing-for-future-ai-capabilities-in-biology/ ; https://internationalaisafetyreport.org/publication/international-ai-safety-report-2025",
        "why_expected": "Biological misuse is high-consequence, hard to observe early, and difficult to reverse once operationalized.",
        "why_observed": "Current safeguards emphasize internal evaluations, monitoring, refusal tuning, and release gating, but not standing third-party verification.",
        "source_summary": "OpenAI's June 18, 2025 biology preparedness post describes capability thresholds, refusal training, always-on detection, monitoring and enforcement, expert red-teaming, security controls, and release gating for models that may reach High biological capability. The International AI Safety Report 2025 likewise treats biological and chemical attacks as a serious emerging risk area and emphasizes the limits of current assessments and safeguards.",
        "mapping_validation": "Observed tier 2 is appropriate because the sources describe structured operational safeguards and monitoring, but these remain primarily developer-run and do not amount to standing independent external verification with access rights.",
    },
    {
        "case": "EU AI Act for GPAI systemic-risk models",
        "domain": "Frontier / systemic-risk AI",
        "instrument_year": 2024,
        "case_type": "Recent AI-linked case",
        "expected_tier": 3,
        "observed_tier": 2,
        "source_title": "EU AI Act systemic-risk obligations",
        "source_url": "https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-55 ; https://digital-strategy.ec.europa.eu/en/faqs/general-purpose-ai-models-ai-act-questions-answers",
        "why_expected": "Systemic-risk frontier models can create large-scale, cross-sector harms that are difficult to monitor through self-reporting alone.",
        "why_observed": "The Act imposes evaluation, incident reporting, documentation, and cybersecurity duties, but not arms-control-style inspection access.",
        "source_summary": "The EU AI Act imposes duties on providers of systemic-risk general-purpose AI models, including model evaluation, adversarial testing, serious-incident reporting, documentation, and cybersecurity protections.",
        "mapping_validation": "Observed tier 2 is appropriate because the regime is more than voluntary dialogue, but it still relies on regulated reporting and compliance duties rather than independent inspection-style verification.",
    },
    {
        "case": "Human-control norm for AI and nuclear use",
        "domain": "Nuclear decision environments",
        "instrument_year": 2024,
        "case_type": "Recent AI-linked case",
        "expected_tier": 3,
        "observed_tier": 1,
        "source_title": "Biden-Xi November 2024 reporting on human control over nuclear-use decisions",
        "source_url": "https://www.cnbc.com/2024/11/17/biden-xi-agree-that-humans-not-ai-should-control-nuclear-arms.html",
        "why_expected": "Nuclear-use decisions sit at the extreme end of catastrophic and irreversible risk.",
        "why_observed": "The current signal is a political norm about human control, not a dedicated verification regime for AI use in nuclear decision chains.",
        "source_summary": "Public reporting on the November 2024 Biden-Xi discussion indicates agreement that humans, not AI, should control decisions on nuclear weapons use.",
        "mapping_validation": "Observed tier 1 is appropriate because the cited material supports a political norm or declaration, not a dedicated oversight architecture with monitoring or verification powers.",
    },
    {
        "case": "IAEA safeguards",
        "domain": "Nuclear safeguards benchmark",
        "instrument_year": 2024,
        "case_type": "Historical / comparator benchmark",
        "expected_tier": 3,
        "observed_tier": 3,
        "source_title": "IAEA safeguards explained",
        "source_url": "https://www.iaea.org/topics/safeguards-explained",
        "why_expected": "Diversion of nuclear material is high-consequence and difficult to rely on trust alone to detect.",
        "why_observed": "IAEA safeguards are built around independent verification and access-based oversight.",
        "source_summary": "IAEA safeguards are designed to verify that states honor commitments not to use nuclear programs for nuclear weapons, using inspections, material accountancy, and monitoring.",
        "mapping_validation": "Observed tier 3 is appropriate because this is a canonical independent verification regime with formal access and inspection authority.",
    },
    {
        "case": "CWC / OPCW challenge inspections",
        "domain": "Chemical weapons benchmark",
        "instrument_year": 2024,
        "case_type": "Historical / comparator benchmark",
        "expected_tier": 3,
        "observed_tier": 3,
        "source_title": "OPCW Chemical Weapons Convention verification framework",
        "source_url": "https://www.opcw.org/chemical-weapons-convention/ ; https://www.opcw.org/chemical-weapons-convention/annexes/verification-annex/part-x-challenge-inspections-pursuant",
        "why_expected": "Chemical weapons present severe humanitarian risk and can require intrusive checks when violations are suspected.",
        "why_observed": "The OPCW regime includes routine verification and challenge-inspection mechanisms.",
        "source_summary": "The Chemical Weapons Convention, as implemented by the OPCW, includes declarations, routine verification, and challenge inspections when compliance concerns arise.",
        "mapping_validation": "Observed tier 3 is appropriate because the regime includes formal external verification and challenge-access mechanisms rather than simple self-reporting.",
    },
]

df = pd.DataFrame(cases)
df["oversight_gap"] = df["expected_tier"] - df["observed_tier"]
df["gap_label"] = df["oversight_gap"].map({0: "Aligned", 1: "Moderate gap", 2: "Large gap"})

csv_path = ANALYSIS_DIR / "ai_oversight_gap_cases.csv"
csv_output_path = write_with_lock_fallback(df, csv_path)

plot_df = df.sort_values(["case_type", "oversight_gap", "observed_tier"], ascending=[False, False, True]).reset_index(drop=True)
y = np.arange(len(plot_df))

fig, ax = plt.subplots(figsize=(13.6, 7.8))
ax.set_facecolor("white")

for i, row in plot_df.iterrows():
    color = PALETTE["red"] if row["oversight_gap"] > 0 else PALETTE["teal"]
    ax.hlines(i, row["observed_tier"], row["expected_tier"], color=color, linewidth=3, zorder=2)
    ax.scatter(row["observed_tier"], i, s=110, color=PALETTE["steel"], zorder=3)
    ax.scatter(row["expected_tier"], i, s=110, color=PALETTE["navy"], zorder=3)

    if row["observed_tier"] == row["expected_tier"]:
        ax.text(
            row["observed_tier"],
            i + 0.24,
            f"obs = exp {row['observed_tier']}",
            fontsize=8.6,
            color=PALETTE["navy"],
            ha="center",
            va="center",
        )
    else:
        ax.text(
            row["observed_tier"] - 0.08,
            i + 0.21,
            f"obs {row['observed_tier']}",
            fontsize=8.8,
            color=PALETTE["steel"],
            ha="right",
            va="center",
        )
        ax.text(
            row["expected_tier"] + 0.08,
            i + 0.21,
            f"exp {row['expected_tier']}",
            fontsize=8.8,
            color=PALETTE["navy"],
            ha="left",
            va="center",
        )

ax.set_yticks(y)
ax.set_yticklabels([textwrap.fill(x, 34) for x in plot_df["case"]], fontsize=9.3, color=PALETTE["dark"])
ax.invert_yaxis()
ax.set_xlim(-0.1, 3.35)
ax.set_xticks([0, 1, 2, 3])
ax.set_xlabel("AMC-style oversight tier", fontsize=10.5)
fig.suptitle(
    "Oversight Gaps in Recent AI-Linked High-Risk Cases",
    fontsize=18,
    fontweight="bold",
    color=PALETTE["navy"],
    y=0.988,
)
fig.text(
    0.5,
    0.948,
    "Observed tier reflects current governance. Expected tier is an analytic benchmark for high-risk, hard-to-observe domains.",
    ha="center",
    va="center",
    fontsize=9.3,
    color="#556070",
)
fig.subplots_adjust(top=0.84)
ax.grid(axis="x", color=PALETTE["light"], linewidth=0.8)
ax.spines[["left", "bottom"]].set_color(PALETTE["light"])

for split_label, split_y in [("Recent AI-linked cases", 1.5), ("Comparator verification regimes", 4.5)]:
    ax.text(-0.08, split_y, split_label, fontsize=9, color=PALETTE["dark"], fontweight="bold", va="center")

from matplotlib.lines import Line2D
legend_items = [
    Line2D([0], [0], marker="o", color="w", label="Observed current tier", markerfacecolor=PALETTE["steel"], markersize=8),
    Line2D([0], [0], marker="o", color="w", label="Expected tier from AMC logic", markerfacecolor=PALETTE["navy"], markersize=8),
    Line2D([0], [0], color=PALETTE["red"], lw=3, label="Oversight gap"),
]
ax.legend(handles=legend_items, loc="lower right", frameon=False, fontsize=8.8)

fig_path = FIG_DIR / "fig8_ai_oversight_gap_cases.png"
fig.savefig(fig_path, dpi=170, bbox_inches="tight", facecolor="white")
plt.close(fig)

recent = df[df["case_type"] == "Recent AI-linked case"].copy()
bench = df[df["case_type"] == "Historical / comparator benchmark"].copy()

summary_lines = [
    "# AI Oversight-Gap Analysis",
    "",
    "This file summarizes a small hand-coded extension to Challenge 8.",
    "",
    "## Method",
    "",
    "The analysis uses the AMC compliance spectrum as a rubric for recent AI-linked governance cases:",
    "",
    "- `0` = no structured mechanism",
    "- `1` = consultation / political dialogue / non-binding declaration",
    "- `2` = structured evaluations, reporting, documentation, or internal monitoring without standing independent verification",
    "- `3` = independent external verification or inspection-style oversight with access rights",
    "",
    "Expected tier is assigned from the logic in `challenge08_compliance_architecture.py`: catastrophic, hard-to-observe, or fast-escalation domains should trend toward tier 3.",
    "",
    "## Main Result",
    "",
    f"Across the {len(recent)} recent AI-linked cases, the mean observed tier is `{recent['observed_tier'].mean():.2f}` versus a mean expected tier of `{recent['expected_tier'].mean():.2f}`, for an average oversight gap of `{recent['oversight_gap'].mean():.2f}` tiers.",
    "",
    "Comparator verification regimes (IAEA safeguards; CWC/OPCW challenge inspections) score `3`, matching the high-risk benchmark in the original Challenge 8 analysis.",
    "",
    "## Case Table",
    "",
    "| Case | Domain | Observed tier | Expected tier | Gap |",
    "|------|--------|---------------|---------------|-----|",
]

for _, row in df.iterrows():
    summary_lines.append(f"| {row['case']} | {row['domain']} | {row['observed_tier']} | {row['expected_tier']} | {row['oversight_gap']} |")

summary_lines += [
    "",
    "## Interpretation",
    "",
    "- The autonomous-weapons and nuclear-AI cases are currently closer to `consultation` than to `verified compliance`.",
    "- The AI-biosecurity and EU systemic-risk cases are stronger than pure consultation, but still stop short of independent verification.",
    "- The gap is therefore not inferred from AMC treaty rows directly; it comes from applying the AMC tier logic to explicitly coded recent cases with cited sources.",
    "",
    "## Validation Notes",
    "",
]

for _, row in df.iterrows():
    summary_lines.append(f"### {row['case']}")
    summary_lines.append("")
    summary_lines.append(f"- **Source summary:** {row['source_summary']}")
    summary_lines.append(f"- **Mapping validation:** {row['mapping_validation']}")
    summary_lines.append("")

summary_lines += [
    "",
    "## Sources",
    "",
]

for _, row in df.iterrows():
    summary_lines.append(f"- **{row['case']}**: {row['source_title']} — {row['source_url']}")

md_path = ANALYSIS_DIR / "challenge08_ai_oversight_gap.md"
md_output_path = write_text_with_lock_fallback(md_path, "\n".join(summary_lines))

print("Saved:", csv_output_path)
print("Saved:", fig_path)
print("Saved:", md_output_path)
print()
print("Recent AI-linked cases:")
print(recent[["case", "observed_tier", "expected_tier", "oversight_gap"]].to_string(index=False))
print()
print(f"Average observed tier (recent AI-linked cases): {recent['observed_tier'].mean():.2f}")
print(f"Average expected tier (recent AI-linked cases): {recent['expected_tier'].mean():.2f}")
print(f"Average oversight gap (recent AI-linked cases): {recent['oversight_gap'].mean():.2f}")
