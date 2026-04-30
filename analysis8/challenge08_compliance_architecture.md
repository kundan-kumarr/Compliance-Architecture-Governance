# The Compliance Architecture Spectrum in Arms Control
## What 80 Years of Treaties Can Teach AI Governance

**Challenge 8 — AMC Research Sprint | April 2026**
*Alva Myrdal Centre for Nuclear Disarmament, Uppsala University*

> **Submission note:** This output covers both **Part A** (empirical analysis + ML extensions,
> Sections 2–5) and **Part B** (AI governance extension, Section 6). LLM text classification
> is documented separately in `challenge08_llm_classification.py`.

---

## 1. Introduction

Not all arms control agreements are built the same. Some rely on political pledges alone; others
build elaborate inspection regimes enforced by independent bodies. The AMC dataset captures this
variation across 128 agreements spanning 1817–2021 through three measurable tiers:
**consultation**, **demonstrated compliance** (self-reporting), and **verified compliance**
(third-party inspection). Understanding how arms control allocates oversight across weapon types
and over time reveals a consistent logic — one with direct relevance to current debates about
tiering AI governance.

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

Scores represent the **highest tier present** in each agreement. Where multiple mechanism
entries exist per agreement, we assign the highest compliance tier observed. Weapon categories
are drawn from the `item` column in the Weapons & Facilities dataset (Summary Category rows),
joined to agreements via `agreement_id`. Time trends are aggregated by decade (1920s–2020s).

**Methodological note — BWC anomaly:** The Biological Weapons Convention (1972) scores 3.0
(verified compliance) because the treaty text includes a verification article. However, a
formal verification protocol was negotiated but ultimately rejected by the US in 2001 and has
never entered into force. The score reflects *treaty design intent*, not operational
effectiveness. This is a known limitation: a high compliance score does not guarantee that the
mechanism functions in practice.

---

## 3. Results

### 3.1 Overall Distribution

Of 128 agreements:
- **39% have no compliance mechanism** — they rely entirely on political goodwill
- 27% have verified compliance (third-party inspection)
- 25% have demonstrated compliance (self-reporting)
- 9% have consultation only

> **Surprising finding:** Nearly 40% of agreements contain no compliance mechanism — meaning
> the international system frequently relies on unenforced promises even in security-critical
> domains. This is a deliberate political choice, but a fragile one: when trust erodes, these
> agreements collapse (e.g., the ABM Treaty, withdrawn 2002; INF Treaty, withdrawn 2019).

### 3.2 Killer Insight: Verification Concentrates in High-Risk Domains

> **States only accept intrusive verification when the cost of undetected cheating is catastrophic.**

This is not accidental. The data show that mean compliance scores fall sharply by risk level:

| Risk Level | Weapon Domain | Mean Compliance Score |
|------------|--------------|----------------------|
| High | Biological & Chemical Weapons | **3.00** (fully verified) |
| High | Strategic delivery systems (ICBMs, SLBMs, Heavy Bombers) | **3.00** (fully verified) |
| Medium-High | Conventional Weapons (Air/Sea) | **1.62–1.67** (mostly demonstrated) |
| Medium | Conventional Weapons (Land) | **1.29** |
| Mixed | Nuclear Weapons (general) | **1.43** (wide variation) |

Strategic nuclear delivery systems — where a single violation could be catastrophic and
irreversible — attract the strongest possible oversight. Conventional weapons, where violations
are more detectable and recoverable, do not.

### 3.3 Time Trend: Rise and Decline of Verified Compliance

The 1970s–1990s were the peak of verified compliance agreements, driven by Cold War arms
control negotiations (SALT, ABM, INF, START, CFE, CWC). Post-2000, both the volume and
strength of new agreements have declined sharply — the 2000s saw no new verified compliance
agreements at all, and the 2010s only two — a reversal reflecting rising great-power mistrust
and the breakdown of bilateral arms control architecture between the US and Russia.

> **Key implication:** The infrastructure for strong compliance was built during a specific
> geopolitical window. When that window closed, the pipeline dried up.

---

## 4. Interpretation

### 4.1 Compliance mechanisms scale with perceived geopolitical risk

Arms control never applied IAEA-style verification uniformly. The pattern is consistent and
deliberate:

| Risk Level | Example Domain | Observed Compliance | Logic |
|------------|---------------|---------------------|-------|
| High | Nuclear weapons (strategic) | Verified | Catastrophic, irreversible; cheating undetectable by other means |
| Medium | Conventional weapons | Demonstrated | Significant but recoverable; self-reporting politically viable |
| Low | General/early treaties | Consultation or none | Low lethality or high existing trust |

States accepted intrusive verification only where the stakes justified it — and where no other
means of detecting violations existed. This pattern suggests that compliance design is not
arbitrary, but follows a consistent risk-based logic across domains.

### 4.2 Self-reporting alone is insufficient at high risk

The CWC and IAEA safeguards both feature *challenge inspections* — the right to demand access
beyond declared facilities when violations are suspected. This design choice reflects a
fundamental lesson from arms control: self-reporting works only when cheating is difficult or
detectable by other means. When it is not, verification must be independent.

### 4.3 The "no mechanism" baseline is fragile

Half of all agreements have no oversight mechanism. They persist on political goodwill. The
history of arms control shows that these agreements are the first to collapse when political
relationships deteriorate. The absence of a mechanism is not a policy-neutral choice —
it is a bet on stable trust.

---

## 5. ML Extensions

Three statistical tests were run to validate and deepen the descriptive findings
(code: `challenge08_ml_extensions.py`).

### 5.1 Ordinal Logistic Regression — What Predicts Verified Compliance?

A multinomial logistic regression (n=128, 4 outcome classes) predicts compliance tier from
treaty year, laterality, log-signatories, log-state-parties, and broad weapon category.

**In-sample accuracy: 53%** (random baseline: ~25–39% for four unequal classes — substantially
above chance given the small sample).

Key findings from the Verified vs. None coefficient contrast:

| Predictor | Direction | Interpretation |
|-----------|-----------|----------------|
| Log(Signatories) | **+0.84** | More parties → stronger oversight demand |
| Strategic delivery weapons | **+0.79** | ICBM/SLBM/bomber treaties drive verification |
| Log(State Parties) | **+0.66** | Larger coalitions sustain verification infrastructure |
| Conventional weapons | **−0.52** | Conventional agreements resist intrusive verification |
| Multilateral format | **−0.59** | Multilateral treaties are harder to verify than bilateral |

The negative multilateral coefficient is the most counterintuitive result: bilateral agreements
(US–USSR/Russia) were actually *more* likely to have verified compliance than multilateral ones.
This reflects the Cold War dyadic dynamic — two adversaries with high stakes and no trust built
the most elaborate verification systems (START, INF, ABM). Multilateral agreements more often
rely on consensus-based consultation.

### 5.2 Hierarchical Clustering — Do Natural Groupings Recover the Tiers?

Ward-linkage clustering with k=4 (matching our four tiers) produces one highly pure cluster:
**Cluster 3 contains 5 verified + 1 demonstrated and zero agreements without mechanisms** —
confirming that a natural grouping exists at the verified-compliance end of the spectrum.

The overall picture is more mixed: Cluster 4, the largest, contains 31 None + 8 Consultation
+ 18 Demonstrated + 14 Verified — a broad middle ground that does not map cleanly onto any
single tier. This reflects the genuine continuum in the data rather than four sharp categories.
The clustering does not fully validate the ordinal scale; what it does show is that **verified
compliance agreements form a statistically distinct cluster**, while the three lower tiers blend
into one another. That is itself a substantive finding: the gap between "some oversight" and
"third-party inspection" is larger than the gaps within the lower tiers.

### 5.3 Change-Point Detection — When Did the Verified Compliance Peak End?

PELT algorithm (RBF cost) applied to the annual count of verified compliance agreements
(1920–2021) detects **two statistically significant breakpoints: 1989 and 1997**.

- **1989** — marks the start of the post-Cold War arms control surge (CFE Treaty, CWC
  negotiations accelerating, START I concluded 1991). Not the end of verified compliance,
  but the beginning of a distinct high-output phase.
- **1997** — formally locates the end of the peak. After 1997 (Ottawa Treaty, CTBT), the
  pipeline of new verified compliance agreements effectively closes. The 2000s produced zero.

This is stronger evidence than eyeballing the decade chart: the decline is not gradual drift
but a detected structural break, consistent with the US withdrawal from the ABM Treaty (2002)
and the subsequent collapse of bilateral arms control architecture.

---

## 6. Short Conclusion: Lessons for AI Governance

Current AI governance is structurally equivalent to the **consultation and demonstration tiers**
of arms control — voluntary commitments, model cards, and industry self-reporting — a design
that arms control history suggests is insufficient for high-risk systems. For frontier AI capabilities with
potential for mass harm or irreversible consequences, the analogy points clearly to a
**verified compliance** model: independent third-party audits, mandatory access, and
challenge inspection rights.

**Three concrete lessons:**

1. **Tier oversight to risk** — reserve the most intrusive mechanisms for the highest-risk
   systems; lighter-touch approaches for lower-risk applications will face less political
   resistance and still provide meaningful accountability.

2. **Build verification infrastructure before it is urgently needed** — the IAEA was
   established in 1957, years before verification became critical. For AI, **interpretability
   review** is the closest functional analogue to challenge inspections: just as inspectors
   demand access to undeclared facilities when violations are suspected, interpretability
   tools must be capable of probing model internals beyond what developers voluntarily
   disclose. Developing those standards now — before a frontier-AI incident forces the
   question — follows the same logic as building the IAEA before the first proliferation
   crisis.

3. **Norms without mechanisms are fragile** — 39% of arms control agreements rely on goodwill
   alone. AI governance frameworks that rely solely on voluntary commitments face the same
   structural fragility: they hold only as long as geopolitical trust holds.

---

---

> **The history of arms control suggests a simple rule: where trust is low and stakes are high,
> verification is not optional — it is the system.**

---

*Analysis based on AMC Arms Control Agreement Database V2 (128 agreements, 1817–2021).*
*Code: `analysis/challenge08_compliance_architecture.py` (descriptive) · `analysis/challenge08_ml_extensions.py` (ML)*
*Figures: `analysis/figures/`*
