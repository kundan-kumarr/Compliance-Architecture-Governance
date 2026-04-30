# What the LLM Adds

No valid LLM classifications are available yet. The current cached LLM results contain API errors, so the empirical comparison is pending. The framework below is still usable in the paper/slides.

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

- Empirical LLM accuracy: pending
- Policy gaps: pending
- Hidden compliance: pending

## Presentation Language

We do not use AI to replace the dataset coding. We use AI to expose where treaty
design appears stronger or weaker than its actual compliance architecture.

## Case Table

See `llm_research_value_cases.csv` for policy-gap, hidden-compliance, and
validity-check examples.
