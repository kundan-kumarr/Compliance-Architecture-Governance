# The Compliance Architecture Spectrum in Arms Control
## What 80 Years of Treaties Can Teach AI Governance

> Challenge#8 - AMC Research Sprint by **Alva Myrdal Centre for Nuclear Disarmament, Uppsala University** | **April 2026**

---

## 1. Introduction

All arms control treaties are not the same. Some depend on political assurances only, while some develop an elaborate system of inspections conducted by third parties. This diversity in arms control treaties is reflected in the AMC data set for 128 treaties between 1817 and 2021 using three levels of arms control, including **consultation**, **self-assurance**, and **inspection**. It is possible to observe a rationale behind the way arms control treats different weapons over time, which may prove useful for contemporary discussions on tiered AI governance.

---

## 2. Method

We construct an ordinal compliance score from three binary variables in the AMC Agreement
Information dataset:

| Score | Level | Variable |
|-------|-------|----------|
| 0 | No mechanism | *(none present)* |
| 1 | Consultation only | `consultation_mechanism` |
| 2 | Demonstrated compliance | `demonstrated_compliance_mechanism` |
| 3 | Verified compliance | `verified_compliance_mechanism` |

Here, Scores represent the **highest tier present** in each agreement. Where multiple mechanism
entries exist per agreement, we assign the highest compliance tier observed. Weapon categories
are drawn from the `item` column in the Weapons & Facilities dataset (Summary Category rows),
joined to agreements via `agreement_id`. Time trends are aggregated by decade (1920s–2020s).

**Methodological note - BWC anomaly:** The Biological Weapons Convention (1972) gets a rating of 3.0 (compliance verified) since there is a verification clause in the text of the treaty. However, there has been a formal verification protocol negotiated but which has never come into effect because the US has refused to ratify it as of 2001. Note that this is simply about *the treaty itself*, not about whether it actually works.

---

## 3. Results

### 3.1 Overall Distribution

Of 128 agreements (Figure 1 - overall distribution):
- **39% have no compliance mechanism** - they rely entirely on political goodwill
- 27% have verified compliance (third-party inspection)
- 25% have demonstrated compliance (self-reporting)
- 9% have consultation only

> **Surprising finding:** Nearly 40% of agreements contain no compliance mechanism - meaning
> the international system frequently relies on unenforced promises even in security-critical
> domains. This is a deliberate political choice, but a fragile one: when trust erodes, these
> agreements collapse (e.g., the ABM Treaty, withdrawn 2002; INF Treaty, withdrawn 2019).

### 3.2 Killer Insight: Verification Concentrates in High-Risk Domains

> **States only accept intrusive verification when the cost of undetected cheating is catastrophic.**

This is not accidental. The data show that mean compliance scores fall sharply by risk level
(Figure 1 - weapon category breakdown, red diamond scores):

| Risk Level | Weapon Domain | Mean Compliance Score |
|------------|--------------|----------------------|
| High | Biological & Chemical Weapons | **3.00** (fully verified) |
| High | Strategic delivery systems (ICBMs, SLBMs, Heavy Bombers) | **3.00** (fully verified) |
| Medium-High | Conventional Weapons (Air/Sea) | **1.62–1.67** (mostly demonstrated) |
| Medium | Conventional Weapons (Land) | **1.29** |
| Mixed | Nuclear Weapons (general) | **1.43** (wide variation) |

Strategic nuclear delivery systems - where a single violation could be catastrophic and
irreversible - attract the strongest possible oversight. Conventional weapons, where violations
are more detectable and recoverable, do not.

### 3.3 Time Trend: Rise and Decline of Verified Compliance

The 1970s–1990s were the peak of verified compliance agreements, driven by Cold War arms
control negotiations (SALT, ABM, INF, START, CFE, CWC), visible clearly in Figure 2 - the
verified compliance line peaks in the 1990s before collapsing to zero in the 2000s. Post-2000,
both the volume and strength of new agreements have declined sharply - the 2000s saw no new
verified compliance agreements at all, and the 2010s only two - a reversal reflecting rising
great-power mistrust and the breakdown of bilateral arms control architecture between the US
and Russia.

> **Key implication:** The infrastructure for strong compliance was built during a specific
> geopolitical window. When that window closed, the pipeline dried up.

---

## 4. Interpretation

### 4.1 Compliance mechanisms scale with perceived geopolitical risk

Arms control never applied IAEA-style verification uniformly. The pattern is consistent and
deliberate (Figure 4 - risk-compliance framework):

| Risk Level | Example Domain | Observed Compliance | Logic |
|------------|---------------|---------------------|-------|
| High | Nuclear weapons (strategic) | Verified | Catastrophic, irreversible; cheating undetectable by other means |
| Medium | Conventional weapons | Demonstrated | Significant but recoverable; self-reporting politically viable |
| Low | General/early treaties | Consultation or none | Low lethality or high existing trust |

States accepted intrusive verification only where the stakes justified it - and where no other
means of detecting violations existed. This pattern suggests that compliance design is not
arbitrary, but follows a consistent risk-based logic across domains.

### 4.2 Self-reporting alone is insufficient at high risk

The CWC and IAEA safeguards both feature *challenge inspections* - the right to demand access
beyond declared facilities when violations are suspected. This design choice reflects a
fundamental lesson from arms control: self-reporting works only when cheating is difficult or
detectable by other means. When it is not, verification must be independent.

### 4.3 The "no mechanism" baseline is fragile

Half of all agreements have no oversight mechanism. They persist on political goodwill. The
history of arms control shows that these agreements are the first to collapse when political
relationships deteriorate. The absence of a mechanism is not a policy-neutral choice -
it is a bet on stable trust.

---

## 5. ML Extensions

Three statistical tests were run to validate and deepen the descriptive findings
(code: `challenge08_ml_extensions.py`).

### 5.1 Ordinal Logistic Regression - What Predicts Verified Compliance?

A multinomial logistic regression (n=128, 4 outcome classes) predicts compliance tier from
treaty year, laterality, log-signatories, log-state-parties, and broad weapon category
(Figure 5 - regression coefficients).

**In-sample accuracy: 53%** (random baseline: ~25–39% for four unequal classes - substantially
above chance given the small sample).

Key findings from the Verified vs. None coefficient contrast:

| Predictor | Direction | Interpretation |
|-----------|-----------|----------------|
| Log(Signatories) | **+0.85** | More parties → stronger oversight demand |
| Strategic delivery weapons | **+0.79** | ICBM/SLBM/bomber treaties drive verification |
| Log(State Parties) | **+0.65** | Larger coalitions sustain verification infrastructure |
| Conventional weapons | **−0.53** | Conventional agreements resist intrusive verification |
| Multilateral format | **−0.59** | Multilateral treaties are harder to verify than bilateral |

The negative multilateral coefficient is the most counterintuitive result: bilateral agreements
(US–USSR/Russia) were actually *more* likely to have verified compliance than multilateral ones.
This reflects the Cold War dyadic dynamic - two adversaries with high stakes and no trust built
the most elaborate verification systems (START, INF, ABM). Multilateral agreements more often
rely on consensus-based consultation.

**Bootstrap stability check (300 resamples, 95% CIs):** To assess whether these point
estimates are stable, we ran 300 bootstrap resamples of the regression. Weapon: Strategic
Delivery (+0.79) and Log(Signatories) (+0.85) are the only predictors whose bootstrap
confidence intervals do not cross zero - confirming them as robust signals. Laterality
(−0.59), Treaty Year (+0.06), and Log(State Parties) show wide intervals crossing zero and
should be treated as directional rather than definitive. The core finding - weapon type and
coalition size predict verified compliance - is stable across resamples; the precise magnitude
of other coefficients is not.

### 5.2 Hierarchical Clustering - Do Natural Groupings Recover the Tiers?

Ward-linkage clustering with k=4 (matching our four tiers) produces one highly pure cluster
(Figure 6 - cluster heatmap with purity profiles): **Cluster 2 contains 13 verified agreements
at 83% purity** - confirming that a natural grouping exists at the verified-compliance end of
the spectrum.

The overall picture is more mixed: Cluster 4, the largest, contains 31 None + 8 Consultation
+ 18 Demonstrated + 14 Verified - a broad middle ground that does not map cleanly onto any
single tier. This reflects the genuine continuum in the data rather than four sharp categories.
The clustering does not fully validate the ordinal scale; what it does show is that **verified
compliance agreements form a statistically distinct cluster**, while the three lower tiers blend
into one another. That is itself a substantive finding: the gap between "some oversight" and
"third-party inspection" is larger than the gaps within the lower tiers.

### 5.3 Change-Point Detection - When Did the Verified Compliance Peak End?

PELT algorithm (RBF cost) applied to the annual count of verified compliance agreements
(1920–2021) detects **two statistically significant breakpoints: 1989 and 1997** (Figure 7 -
change-point time series with 5-year rolling mean).

- **1989** - marks the start of the post-Cold War arms control surge (CFE Treaty, CWC
  negotiations accelerating, START I concluded 1991). Not the end of verified compliance,
  but the beginning of a distinct high-output phase.
- **1997** - formally locates the end of the peak. After 1997 (Ottawa Treaty, CTBT), the
  pipeline of new verified compliance agreements effectively closes. The 2000s produced zero.

This is stronger evidence than eyeballing the decade chart: the decline is not gradual drift
but a detected structural break, consistent with the US withdrawal from the ABM Treaty (2002)
and the subsequent collapse of bilateral arms control architecture.

---

## 6. Short Conclusion: Lessons for AI Governance

Current AI governance is structurally equivalent to the **consultation and demonstration tiers**
of arms control - voluntary commitments, model cards, and industry self-reporting - a design
that arms control history suggests is insufficient for high-risk systems. For frontier AI capabilities with
potential for mass harm or irreversible consequences, the analogy points clearly to a
**verified compliance** model: independent third-party audits, mandatory access, and
challenge inspection rights.

**Three concrete lessons:**

1. **Tier oversight to risk** - reserve the most intrusive mechanisms for the highest-risk
   systems; lighter-touch approaches for lower-risk applications will face less political
   resistance and still provide meaningful accountability.

2. **Build verification infrastructure before it is urgently needed** - the IAEA was
   established in 1957, years before verification became critical. For AI, **interpretability
   review** is the closest functional analogue to challenge inspections: just as inspectors
   demand access to undeclared facilities when violations are suspected, interpretability
   tools must be capable of probing model internals beyond what developers voluntarily
   disclose. Developing those standards now - before a frontier-AI incident forces the
   question - follows the same logic as building the IAEA before the first proliferation
   crisis.

3. **Norms without mechanisms are fragile** - 39% of arms control agreements rely on goodwill
   alone. AI governance frameworks that rely solely on voluntary commitments face the same
   structural fragility: they hold only as long as geopolitical trust holds.

### 6.4 Applying the AMC Rubric to Current AI Governance

The compliance tier logic established in Part A can be applied directly to current AI-linked
governance instruments. Using the same 0–3 ordinal scale - where 0 = no mechanism,
1 = consultation, 2 = demonstrated compliance, 3 = verified compliance - four high-risk AI
governance cases score an average observed tier of **1.50** against an expected tier of
**3.00** for catastrophic, hard-to-observe domains. The two arms control benchmarks score 3,
matching the high-risk standard in Part A (Figure 8).

| Case | Domain | Observed | Expected | Gap |
|------|--------|----------|----------|-----|
| UN autonomous weapons process | Autonomous weapons | 1 | 3 | −2 |
| AI-biosecurity preparedness | AI-biosecurity / dual-use biology | 2 | 3 | −1 |
| EU AI Act - GPAI systemic risk | Frontier AI | 2 | 3 | −1 |
| Human-control norm, AI and nuclear use | Nuclear decision environments | 1 | 3 | −2 |
| **IAEA safeguards** *(benchmark)* | Nuclear safeguards | 3 | 3 | 0 |
| **CWC/OPCW** *(benchmark)* | Chemical weapons | 3 | 3 | 0 |

The two largest gaps - autonomous weapons (−2) and AI in nuclear decision environments (−2)
- are precisely the domains where arms control history predicts consultation-only governance
is most fragile. The AI-biosecurity and EU AI Act cases are stronger - structured evaluation
and reporting obligations exist - but they remain at Tier 2. What is missing in all four cases
is the independent access right that defines Tier 3: the ability of an external body to demand
inspection beyond what developers or states voluntarily disclose. The CWC built that right in
1993; the IAEA Additional Protocol in 1997. AI governance has not built it anywhere yet.

**Why the autonomous weapons gap matters - and what verification would require.**
The February 2026 strike on the Shajareh Tayyebeh girls' school in Minab, Iran - in which
approximately 165 children were killed - illustrates the governance gap concretely. Attribution
remains disputed months after the incident: Iran has blamed the US and Israel; the US has
denied deliberate targeting; social media claims of an Iranian own-strike have been
fact-checked as false (Bellingcat, NYT, Washington Post investigations point to a US Tomahawk
missile based on visual analysis, though no official confirmation exists). Some expert
commentary has raised the question of whether AI-assisted targeting systems may have
contributed to the strike - *this remains unconfirmed speculation and is not established
fact.* What is established is the governance conclusion: **no independent verification
mechanism exists with access rights to targeting logs, strike authorization chains, or
AI system inputs.** Whether or not AI was involved in this specific case cannot be determined
because the oversight architecture to determine it does not exist.

This is precisely what a Tier 1 governance situation looks like in practice: a political norm
- "humans control lethal autonomous decisions" - with no verification architecture to confirm
or deny compliance after an incident. The CWC analogy is direct. Before 1993, chemical weapons
use in conflict was similarly unverifiable after the fact. The OPCW was built specifically to
close that gap. The autonomous weapons domain currently has no equivalent.

> *Note on sourcing: The Minab strike is cited solely for the governance illustration - the
> absence of a verification mechanism that could determine what happened. AI involvement in
> targeting is not confirmed and is explicitly not asserted here. Sources: UK Fact Check
> Politics (March 2026); Snopes (March 3, 2026); FactCheck.org (March 10, 2026); AP News;
> PolitiFact (March 1, 2026).*

---

---

> **The history of arms control suggests a simple rule: where trust is low and stakes are high,
> verification is not optional - it is the system.**

---

---

**Figure inventory (8 figures):**
1. `fig1_compliance_overview.png` - Overall distribution (donut) + compliance by weapon category with mean scores
2. `fig2_compliance_over_time.png` - Compliance architecture by decade with verified compliance trend line
3. `fig3_treaty_examples.png` - Concrete treaty examples per compliance tier with key limitations
4. `fig4_risk_compliance_framework.png` - Risk level → observed compliance → AI governance analogue
5. `fig5_regression_coefficients.png` - Logistic regression coefficients (Verified vs. None contrast)
6. `fig6_clustering_heatmap.png` - Hierarchical clustering heatmap with cluster purity profiles
7. `fig7_changepoint_timeseries.png` - PELT change-point detection with 5-year rolling mean
8. `fig8_ai_oversight_gap_cases.png` - AI oversight gap: observed vs expected tier across current governance instruments

---

*Analysis based on AMC Arms Control Agreement Database V2 (128 agreements, 1817–2021).*
*Code: `analysis/challenge08_compliance_architecture.py` (descriptive) · `analysis/challenge08_ml_extensions.py` (ML)*
*Figures: `analysis/figures/`*
