# AVR — Answer Visibility & Readiness

A diagnostic specification for **AEO** (Answer Engine Optimization): measuring whether a
brand appears in AI-generated answers, and — separately — *why it doesn't*.

**Canon versions:** rubric `1.6.0` · scoring `1.1.0` · channels `1.0.0` · schema `1.2.0`
**Status:** specification frozen · reference implementation running · 3 pilot rounds completed
**License:** [CC BY 4.0](LICENSE) — use, modify, and sell derivatives freely; just credit the source.

> **한국어 문서:** [README.ko.md](README.ko.md). The specification documents in
> `spec/`, `ARCHITECTURE.md`, `CONFORMANCE.md`, `GOVERNANCE.md`, `ADOPTION.md` and
> `STANDARDS.md` are
> currently Korean-only. The machine-readable canon — `rubric/*.yaml`, `schema/`,
> `conformance/cases/*.json` — is language-independent and is what an implementation
> actually consumes.

---

## Why this exists

Most AI-visibility products report a single bare percentage: *"your brand appears in 33% of
answers."* Two things are wrong with that.

**First, the number has no error bar.** AI answers are non-deterministic. Independent
research (Fishkin & O'Donnell, 2,961 prompts across 12 categories) found that fewer than
1 in 100 repeated runs produced the same brand list, and fewer than 1 in 1,000 produced
the same list in the same order. A point estimate without an interval invites reading noise
as change.

**Second, one number cannot say why.** "You score 33%" is not actionable. Whether the fix
is a `robots.txt` line, a content page, or an entity link depends on *which layer is blocked* —
and a visibility score alone cannot distinguish them.

AVR addresses both by separating measurement into two planes and by requiring an interval
on every ratio it emits.

---

## The model

### Two planes

| | Plane A — Visibility | Plane B — Readiness |
|---|---|---|
| Method | Black box. Probe real LLMs, observe answers. | White box. Politely crawl the site, score 45 items. |
| Looks at | The answer | The site |
| Metrics | MR · SoV · PosScore · CitShare | 5 pillars, 45 items |
| Output | **AVI** 0–100 | **ARS** 0–100 |
| Cost | LLM calls (metered) | Crawl only (no LLM cost) |

Neither plane alone produces a prescription. Their intersection does.

### Gap Matrix

```
                 ARS low                    ARS high
AVI high    coasting                   leader
            visible, but the site      both high
            leaks the traffic          → defend, keep fresh

AVI low     untapped                   prepared
            both low                   site is fine, still invisible
            → start at layer 1         → external authority, entity links
```

`prepared` and `untapped` have **opposite** prescriptions. Conflating them sends a customer's
budget in exactly the wrong direction — which is the practical reason the two planes are
measured separately rather than blended into one score.

Thresholds live in `rubric/scoring.yaml`: `avi_threshold: 25.0`, `ars_threshold: 60.0`.
**Both are current estimates**, not cohort-calibrated values. The specification requires a
30-brand cohort to calibrate them; that work is not finished, and reports must disclose this.

### Three layers (Plane B structure)

Each layer is necessary for the next, and none is sufficient.

| Layer | Question | Pillar | Weight |
|---|---|---|---|
| 1. Retrieval | Can an AI crawler reach the page? | P1 접근성 (accessibility) | 25 |
| 2. Selection | Does this page get picked for that query? | P2 추출성 (extractability) | 25 |
| 3. Citation | Does it enter the answer and get cited? | P3 기계가독성 (machine readability) | 20 |
| | | P4 권위 (authority) | 20 |
| | | P5 신선도·운영 (freshness & operations) | 10 |

Layer 1 is roughly a day's work — which is why most AEO products stop there. It is a
necessary condition, not a sufficient one.

---

## Hard invariants

These are load-bearing. An implementation that violates any of them is not AVR-conformant,
and each is enforced by cases in `conformance/`.

| Invariant | Value | Why it cannot move |
|---|---|---|
| Pillar weights sum | `= 100`, integers only | Decimals make float-tolerance checks slack, and slack checks miss real errors |
| Channel weights sum | `= 1.0` | Unmeasured channels are renormalized and `coverage` is disclosed separately |
| Blocking items | **exactly 2** (`P1-01`, `P1-03`) | Not an extension point. Adding a third is a MAJOR version change |
| Gating cap | `40` when a blocking item scores 0 | Applied as `min(score, 40)`, never as assignment |
| Unmeasured ≠ zero | Excluded from the denominator, reason disclosed | Scoring "we couldn't check" as "it's absent" makes a *less audited* site look worse |
| Blocking must be scored | `require_blocking_scored: true` | Otherwise skipping the audit dodges gating — measured at ARS 40 vs 100 |

### The last two, in detail

**Unmeasured is not zero.** Every unscored item carries an `unavailable_kind` (six values,
`schema/report.schema.json` → `$defs.unavailable_kind`):

| kind | meaning | in coverage denominator? |
|---|---|---|
| `not_applicable` | The thing being judged does not exist on this site | **excluded** |
| `design_limit` | Undecidable in principle from a single observation | **excluded** |
| `inconclusive` | It exists, but the check failed | retained |
| `no_collector` | The implementation hasn't built this check yet | retained |
| `input_missing` | A required input wasn't supplied | retained |
| `awaiting_manual` | A `check: manual` item with no human verdict yet | retained |

One rule decides the split: **if the subject of judgment does not exist on the site, drop it;
if we simply don't know, keep it.** When it's ambiguous, keep — dropping inflates coverage.

**Blocking items are the exception.** Gating only fires at level 0, so *not measuring* a
blocking item would evade it. Blocking items must be scored, or declared unavailable with an
explicit reason (which sets `gating_undetermined: true`); a silent omission is rejected.
`not_applicable` and `design_limit` are forbidden kinds for blocking items, because those are
exactly the two that leave the denominator.

---

## Statistical requirements

This is the part most implementations skip, and it is the part that makes the output usable.

**1. Every ratio ships with an interval.** Not `33%` but `33% ± 4.2%p (n=400, 95% CI)`.
Wilson score interval, `z = 1.959964` (`rubric/scoring.yaml` → `statistics.default_z`).
Not `1.96` — the rounded value diverges from a correct implementation by ~6.4e-6, and a
conformance case pins this.

**2. Cluster correction is mandatory.** Probing is *M questions × k repeats*, so observations
are not independent. Use the Kish design effect:

```
DEFF  = 1 + (k − 1) · ρ
n_eff = n / DEFF
```

Compute the interval on `n_eff`, and report `n`, `n_eff` and `ρ` together. Skipping this
yields an interval about **63%** of its true width at ρ=0.5, k=4 — and an interval that is
too narrow is worse than no interval, because it certifies precision that isn't there.

**3. Improvement claims require a significance test — on the effective sample.**
Two-proportion z-test. If the intervals overlap, do not call it an improvement. But the
test is only as good as its denominator: probing is *questions × models × repeats*, so
observations are not independent, and the raw `n` overstates what you know.

A worked example is in `conformance/cases/stat-two-proportion-clustered-flips-significance.json`.
A publicly claimed `35.4% → 40.6%` improvement over **3,141 matched pairs** is
`p = 2.3e-05` uncorrected — clearly significant. Correct for clustering at the publisher's
own channel count (k=12) and a moderate intraclass correlation (ρ=0.5) and the effective
sample falls to `n_eff = 483`, where `p = 0.097` — no longer significant.

The point is not that the claim is false. **The point is that without a disclosed ρ,
neither the publisher nor the reader can tell.** That is why AVR requires `n`, `n_eff`
and `ρ` to ship together with every ratio. An improvement claim missing any of the three
is unverifiable, and selling an unverifiable claim as a result is the failure this model
exists to prevent.

**4. Sample size is computable, so compute it.** For ±5%p at p=0.5, `n ≥ 385`; multiply by
DEFF when clustered. "Not enough sample to decide" is a valid, expected result — say it
rather than reporting a point estimate that cannot support the claim.

### AVI

```
AVI = 100 × Σ_c w'_c · (α·MR_c + β·PosScore_c + γ·CitShare_c)
α = 0.5,  β = 0.3,  γ = 0.2   (α ≥ β ≥ γ; MR is the necessary condition, so it dominates)
```

`w'_c` are channel weights renormalized over *measured* channels. If `CitShare` is `null`
for a channel — not zero, `null` — that channel renormalizes to `α' = 0.625, β' = 0.375`.
Citations absent and citations unmeasured are different facts.

### ARS

Each pillar is normalized by the items actually scored, so adding an item automatically
reduces each item's share rather than inflating the pillar:

```
pillar_score = weight × (raw / max_raw),   max_raw = max_level × scored_item_count
max_level = 2
```

A pillar whose coverage falls below `min_pillar_coverage` (0.5) is **not reported**; its
weight is removed and the remainder renormalized to 100. Below `min_item_coverage` (0.7)
overall, the quadrant verdict is flagged `borderline` and the adjacent quadrant's
prescription is printed alongside.

---

## Repository contents

```
README.md  README.ko.md  LICENSE
ARCHITECTURE.md      layering, dependency direction, known gaps
CONFORMANCE.md       adapter contract, tolerances, how to self-declare
DECLARATION.md       our own conformance self-declaration — Level 2, with the
                     numbers a third party can check and what we do NOT claim
GOVERNANCE.md        versioning rules, what forces MAJOR
ADOPTION.md          implementation guide
STANDARDS.md         what is and is not a standard in AEO (surveyed 2026-09-10)
spec/
  avr-model.md            the two-plane model and why it is split
  plane-a-visibility.md   MR · SoV · PosScore · CitShare, probe statuses
  plane-b-readiness.md    5 pillars, 45 items, coverage, unavailable_kind
  scoring.md              AVI/ARS formulas, thresholds, Gap Matrix
  reliability.md          how an implementation measures and discloses its own
                          reproducibility — determinism, time sensitivity, test-retest
rubric/
  pillars.yaml     1.9.0  scoring canon — 5 pillars, 45 items, gating
  channels.yaml    1.2.0  6 channels, weights summing to 1.0
  scoring.yaml     1.1.0  thresholds and coefficients
schema/
  report.schema.json  1.3.0  the report output contract
conformance/
  cases/  94 golden cases
```

### What is **not** here

The reference implementation (collectors, scoring engine, probing pipeline), the
measurement cohort, pilot data, and calibrated threshold values are not in this repository
and are not licensed here.

---

## Implementing AVR

1. **Parse the canon, don't copy it.** Load `rubric/*.yaml` at runtime. If changing a weight
   in the YAML doesn't change your output, you have duplicated the numbers into code — the
   single most common way a scoring implementation drifts from its own specification.
2. **Emit reports that validate against `schema/report.schema.json`.** The report must carry
   `rubric_version`, `channels_version` and `scoring_version`. Without them, a score cannot be
   compared to a past score, and a rubric change will be read as an improvement.
3. **Run the conformance suite.** See `CONFORMANCE.md` §3 for the adapter contract.

### Conformance

Self-declared. There is no certifying body and no badge issued by MKII — a public suite and
an honest declaration are proportionate at this scale.

Expected values in `conformance/cases/` are **derived independently from the formulas in
`spec/`**, never by running the reference implementation and recording what came out. That
distinction matters: expectations captured from an implementation encode that
implementation's bugs as the standard. When the reference implementation disagrees with a
case, the implementation is what gets fixed.

Tolerances (`CONFORMANCE.md` §4): ARS/AVI/Wilson `1e-9`; z and p-values `1e-6`; sample sizes
and item scores exactly `0` (they are integers). `NaN` always fails. Widening a tolerance to
make a case pass stops that case from testing anything.

Cases carrying `"reference_implementation": {"status": "known_gap"}` are ones where the
specification is right and the reference implementation has not caught up. They are expected
to fail; a runner should treat them as strict-xfail so that fixing the implementation
surfaces as an unexpected pass rather than silently turning green.

---

## Versioning

Semantic versioning, three components, per file. `GOVERNANCE.md` has the full rules.

- **MAJOR** — scores are no longer comparable to prior versions: removing an item, moving
  weight between pillars, changing gating, changing channel weights, changing α/β/γ or
  `max_level`.
- **MINOR** — comparable with a caveat: adding an item, adjusting level boundaries or
  thresholds.
- **PATCH** — wording only, confirmed to have no effect on any score.

Every version bump records a `comparability` string in the file's changelog, stating whether
past scores can still be placed beside new ones. That sentence is meant to be reproduced
verbatim in reports.

**Threshold changes are not applied retroactively.** A report carries the `scoring_version`
it was produced under. Otherwise the same score silently lands in a different quadrant, and
nobody can explain why the prescription changed.

---

## Known limits (stated, not hidden)

- `AVI ≥ 25` and `ARS ≥ 60` are **estimates**. Cohort calibration is incomplete.
- Naver AI Briefing (weight 0.18) and Google AI Overviews (weight 0.08) have no official API.
  **26% of channel weight is unmeasurable**, and `coverage` must be reported alongside AVI.
- Weekly tracking uses cheaper models than the flagships consumers actually use. The
  resulting **proxy gap δ** must be measured by monthly calibration and printed in the report.
  An unmeasured δ means a biased number sold as an unbiased one.
- The three-layer causal path is **suggested, not established** — `p = 0.083`, 95% CI
  `[20.8%, 93.9%]` at n=3. Do not write "proven".
- Channel weights are informed estimates adapted from a competitor's published figures, not
  measured Korean market share. `channels.yaml` marks each with `(추정)` — "estimated".
- `PosScore` measures positional rank, which the non-determinism research above argues is the
  least reliable of the four Plane A metrics. Its coefficient warrants review.

Sites named in the specification's worked examples appear as **Site A / B / C**. They are
real pilot measurements, not invented illustrations; they are anonymized because they were
audited without prior notice.

---

## License and attribution

[CC BY 4.0](LICENSE). Share and adapt, commercially included, with attribution:

```
AVR framework (https://github.com/maior/logosai-avr) by MKII, licensed under CC BY 4.0.
```

Scores produced by a third-party implementation are that implementation's own. Conformance
is self-declared and is not a certification issued by MKII.

Built by **[MKII](https://mkiicorp.com)** — AI infrastructure, Seoul, South Korea.
