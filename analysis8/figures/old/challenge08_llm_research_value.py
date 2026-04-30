"""
Challenge 8 - What the LLM Adds
AMC Research Sprint | April 2026

This script turns the LLM comparison into a research-methods artifact.

The LLM is not treated as ground truth. AMC human coding remains the reference.
The LLM is used as an outside reader: given only surface treaty cues, does it
expect the same compliance architecture that AMC researchers coded manually?

Outputs:
  figures/llm_research_value_framework.png
  llm_research_value_summary.md
  llm_research_value_cases.csv
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ANALYSIS_DIR = Path(__file__).resolve().parent
FIG_DIR = ANALYSIS_DIR / "figures"
FIG_DIR.mkdir(exist_ok=True)

LLM_RESULTS = ANALYSIS_DIR / "llm_classification_results.csv"
OUT_MD = ANALYSIS_DIR / "llm_research_value_summary.md"
OUT_CSV = ANALYSIS_DIR / "llm_research_value_cases.csv"

TIER_LABELS = {
    0: "None",
    1: "Consultation",
    2: "Demonstrated",
    3: "Verified",
}


def load_valid_llm_results() -> pd.DataFrame:
    """Load cached LLM classifications, keeping only successful rows."""
    if not LLM_RESULTS.exists():
        return pd.DataFrame()

    results = pd.read_csv(LLM_RESULTS)
    required = {"actual_score", "llm_score"}
    if not required.issubset(results.columns):
        return pd.DataFrame()

    valid = results[results["llm_score"] >= 0].copy()
    if valid.empty:
        return valid

    valid["actual_label"] = valid["actual_score"].map(TIER_LABELS)
    valid["llm_label"] = valid["llm_score"].map(TIER_LABELS)
    valid["off_by"] = valid["actual_score"] - valid["llm_score"]
    valid["match"] = valid["actual_score"] == valid["llm_score"]

    def classify_disagreement(row: pd.Series) -> str:
        if row["llm_score"] > row["actual_score"]:
            return "Policy gap"
        if row["llm_score"] < row["actual_score"]:
            return "Hidden compliance"
        return "Match"

    valid["research_signal"] = valid.apply(classify_disagreement, axis=1)
    return valid


def build_cases(valid: pd.DataFrame) -> pd.DataFrame:
    """Create a case table from real LLM results or a methods placeholder."""
    columns = [
        "research_signal",
        "meaning",
        "agreement_id",
        "title_short",
        "year",
        "actual_label",
        "llm_label",
        "interpretation",
    ]

    if valid.empty:
        rows = [
            {
                "research_signal": "Policy gap",
                "meaning": "LLM expects stronger oversight than AMC coding shows.",
                "agreement_id": "",
                "title_short": "Pending valid LLM classifications",
                "year": "",
                "actual_label": "Lower AMC tier",
                "llm_label": "Higher LLM tier",
                "interpretation": (
                    "Treaty appears ambitious from surface cues, but coded "
                    "architecture lacks equivalent operational machinery."
                ),
            },
            {
                "research_signal": "Hidden compliance",
                "meaning": "AMC coding shows stronger oversight than the LLM expects.",
                "agreement_id": "",
                "title_short": "Pending valid LLM classifications",
                "year": "",
                "actual_label": "Higher AMC tier",
                "llm_label": "Lower LLM tier",
                "interpretation": (
                    "Compliance machinery exists, but it is not obvious from "
                    "treaty name, weapon category, or brief definitions alone."
                ),
            },
            {
                "research_signal": "Validity check",
                "meaning": "LLM and AMC coding agree.",
                "agreement_id": "",
                "title_short": "Pending valid LLM classifications",
                "year": "",
                "actual_label": "Same tier",
                "llm_label": "Same tier",
                "interpretation": (
                    "Surface treaty cues align with the human-coded compliance "
                    "architecture."
                ),
            },
        ]
        return pd.DataFrame(rows, columns=columns)

    policy_gaps = valid[valid["research_signal"] == "Policy gap"].copy()
    hidden = valid[valid["research_signal"] == "Hidden compliance"].copy()
    matches = valid[valid["research_signal"] == "Match"].copy()

    case_df = pd.concat(
        [
            policy_gaps.sort_values(["llm_score", "actual_score"], ascending=[False, True]).head(8),
            hidden.sort_values(["actual_score", "llm_score"], ascending=[False, True]).head(8),
            matches.sort_values("year").head(5),
        ],
        ignore_index=True,
    )

    case_df["meaning"] = case_df["research_signal"].map(
        {
            "Policy gap": "LLM expects stronger oversight than AMC coding shows.",
            "Hidden compliance": "AMC coding shows stronger oversight than the LLM expects.",
            "Match": "LLM and AMC coding agree.",
        }
    )
    case_df["interpretation"] = case_df["research_signal"].map(
        {
            "Policy gap": (
                "Strong legal or political ambition may be more visible than "
                "the actual compliance mechanism."
            ),
            "Hidden compliance": (
                "Domain coding captures institutional detail that surface-level "
                "text does not reveal."
            ),
            "Match": (
                "Human coding aligns with the intuitive signals visible in the "
                "treaty metadata."
            ),
        }
    )
    return case_df[columns]


def write_summary(valid: pd.DataFrame) -> None:
    """Write a concise markdown explanation for the research sprint."""
    if valid.empty:
        status = (
            "No valid LLM classifications are available yet. The current cached "
            "LLM results contain API errors, so the empirical comparison is "
            "pending. The framework below is still usable in the paper/slides."
        )
        metrics = "- Empirical LLM accuracy: pending\n- Policy gaps: pending\n- Hidden compliance: pending"
    else:
        exact = valid["match"].mean()
        within_one = (valid["off_by"].abs() <= 1).mean()
        counts = valid["research_signal"].value_counts()
        metrics = "\n".join(
            [
                f"- Valid classifications: {len(valid)}",
                f"- Exact agreement with AMC coding: {exact:.0%}",
                f"- Within one tier: {within_one:.0%}",
                f"- Policy gaps: {counts.get('Policy gap', 0)}",
                f"- Hidden compliance: {counts.get('Hidden compliance', 0)}",
                f"- Matches: {counts.get('Match', 0)}",
            ]
        )
        status = "Valid LLM classifications are available and summarized below."

    body = f"""# What the LLM Adds

{status}

## Core Idea

The LLM is not used as ground truth. AMC human coding remains the reference.
The LLM is used as an outside reader: given only treaty name, weapon category,
and definitions, can it infer the same compliance tier that AMC researchers
coded manually?

## Research Signals

Policy gap: the LLM predicts a higher compliance tier than AMC coding. This
suggests that the treaty sounds like it should have stronger oversight, but the
coded architecture shows weaker operational machinery.

Hidden compliance: AMC coding is higher than the LLM prediction. This suggests
that real compliance machinery exists, but it is not legible from surface treaty
cues alone.

Validity check: the LLM and AMC coding agree. This supports the claim that the
human-coded tier is visible in the treaty's basic design signals.

## Empirical Status

{metrics}

## Presentation Language

We do not use AI to replace the dataset coding. We use AI to expose where treaty
design appears stronger or weaker than its actual compliance architecture.

## Case Table

See `llm_research_value_cases.csv` for policy-gap, hidden-compliance, and
validity-check examples.
"""
    OUT_MD.write_text(body, encoding="utf-8")


def draw_framework(valid: pd.DataFrame) -> None:
    """Draw a slide-ready figure showing how to interpret LLM disagreement."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 7), gridspec_kw={"width_ratios": [1, 1.15]})
    ax_flow, ax_bar = axes

    ax_flow.axis("off")
    boxes = [
        ("Input to LLM", "Treaty name\nWeapon category\nDefinitions only", 0.08, 0.72, "#eef3f8"),
        ("Outside Reader", "LLM predicts expected\ncompliance tier", 0.38, 0.72, "#eef3f8"),
        ("Reference Coding", "AMC human-coded\ncompliance tier", 0.68, 0.72, "#eef3f8"),
        ("Policy Gap", "LLM higher than AMC\nAmbition outruns machinery", 0.08, 0.28, "#f8e8e6"),
        ("Hidden Compliance", "AMC higher than LLM\nInstitutional detail is hidden", 0.38, 0.28, "#fff0df"),
        ("Validity Check", "LLM and AMC agree\nSurface cues align with coding", 0.68, 0.28, "#e6f1f5"),
    ]
    for title, text, x, y, color in boxes:
        rect = plt.Rectangle((x, y), 0.24, 0.17, transform=ax_flow.transAxes,
                             facecolor=color, edgecolor="#555", linewidth=1.0)
        ax_flow.add_patch(rect)
        ax_flow.text(x + 0.12, y + 0.12, title, transform=ax_flow.transAxes,
                     ha="center", va="center", fontsize=10, fontweight="bold")
        ax_flow.text(x + 0.12, y + 0.055, text, transform=ax_flow.transAxes,
                     ha="center", va="center", fontsize=8.5, color="#333")

    for x0, x1, y in [(0.32, 0.38, 0.805), (0.62, 0.68, 0.805)]:
        ax_flow.annotate("", xy=(x1, y), xytext=(x0, y), xycoords=ax_flow.transAxes,
                         arrowprops=dict(arrowstyle="->", color="#555", lw=1.4))
    ax_flow.text(0.5, 0.55, "Compare predictions to coding", transform=ax_flow.transAxes,
                 ha="center", fontsize=11, fontweight="bold")
    for x in [0.20, 0.50, 0.80]:
        ax_flow.annotate("", xy=(x, 0.45), xytext=(x, 0.70), xycoords=ax_flow.transAxes,
                         arrowprops=dict(arrowstyle="->", color="#777", lw=1.2))

    if valid.empty:
        labels = ["Policy gap", "Hidden compliance", "Match"]
        values = [0, 0, 0]
        subtitle = "Empirical counts pending: current cache has no valid LLM calls"
    else:
        counts = valid["research_signal"].value_counts()
        labels = ["Policy gap", "Hidden compliance", "Match"]
        values = [counts.get(label, 0) for label in labels]
        exact = valid["match"].mean()
        subtitle = f"Valid classifications: {len(valid)} | Exact agreement: {exact:.0%}"

    colors = ["#c0392b", "#e67e22", "#1a5e7a"]
    bars = ax_bar.barh(labels, values, color=colors, edgecolor="white", height=0.5)
    for bar, value in zip(bars, values):
        ax_bar.text(value + 0.3, bar.get_y() + bar.get_height() / 2,
                    str(int(value)), va="center", fontsize=11, fontweight="bold")
    ax_bar.set_xlim(0, max(1, max(values)) * 1.25)
    ax_bar.set_xlabel("Number of agreements", fontsize=10)
    ax_bar.set_title("Empirical Research Signals\n" + subtitle,
                     fontsize=12, fontweight="bold", pad=12)
    ax_bar.spines[["top", "right"]].set_visible(False)

    fig.suptitle("What the LLM Adds: Disagreement as a Research Signal",
                 fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(FIG_DIR / "llm_research_value_framework.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    valid = load_valid_llm_results()
    cases = build_cases(valid)
    cases.to_csv(OUT_CSV, index=False)
    write_summary(valid)
    draw_framework(valid)

    print("Saved: figures/llm_research_value_framework.png")
    print("Saved: llm_research_value_summary.md")
    print("Saved: llm_research_value_cases.csv")
    if valid.empty:
        print("Note: no valid LLM classifications found; framework outputs use pending placeholders.")
    else:
        print(f"Valid LLM classifications summarized: {len(valid)}")


if __name__ == "__main__":
    main()
