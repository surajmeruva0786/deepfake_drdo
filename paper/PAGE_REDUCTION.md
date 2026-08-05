# Page-Reduction Pass on `main.tex`

Date: 2026-08-05

## Goal

The venue's page limit is 4–6 pages. Before this pass, `main.tex` compiled to roughly
6.3 pages: the last few lines of the Conclusion and the whole references list spilled
onto page 7. The target was to reclaim **~0.3 pages** — enough to pull everything back
onto page 6, but not so much that page 6 ends up half empty. We are aiming to *fill*
6 pages, not to shrink below them.

## Constraints held throughout

- **No results changed.** Every metric, table value, figure, and claim is identical.
- **All 6 figures kept** (1 full-width architecture + 5 single-column).
- **All 4 tables kept**, including Table II (the AND-gate truth table), which was
  considered for removal and explicitly retained.
- **No references removed.**

## Changes

### 1. Typography and float spacing (no content change)

| Change | Location | Est. reclaimed |
|---|---|---|
| Float separations reverted to IEEEtran defaults | preamble | ~90 pt |
| Display-equation skips tightened | preamble | ~16 pt |
| `\itemsep`/`\parskip` zeroed in the contributions list | Introduction | ~14 pt |

The float separations had been deliberately set *above* the IEEEtran defaults
(`\floatsep` 14 pt vs. 8 pt, `\textfloatsep` 18 pt vs. 10 pt, `\intextsep` 12 pt vs.
8 pt). With ~10 floats in the paper this was the single largest recoverable block of
whitespace. They are now at the class defaults, which is still standard IEEE spacing.

### 2. Figure scaling (no content change)

| Figure | Was | Now | Reason |
|---|---|---|---|
| `confusion_matrices_unseen.jpg` | `\linewidth` | `0.85\linewidth` | 1570×1600 — nearly square, so it was the tallest single-column float at ~38% of a column |
| `metrics_unseen_forest.jpg` | `\linewidth` | `0.9\linewidth` | 1600×1010 |

Combined: ~55 pt. Both remain legible at these widths.

### 3. Prose compression (~160 words)

| Section | Words before → after | What was cut |
|---|---|---|
| Abstract | 335 → 308 | Restatements of the PGCF/AGCF mirroring; per-model "achieves an AUC of" repeated four times, collapsed. Also removed "calibration curves" from the closing list — **that claim was stale**, since the calibration figure is no longer in the paper. |
| Introduction | 549 → 514 | Phrasing in ¶3–4 that duplicated the abstract's description of the mirrored architecture; 4th contribution bullet tightened. |
| Methodology III-B | 346 → 335 | "Spectral Stream" and "Vocal Stream" merged into one subsubsection, "Spectral and Vocal Streams". Both had only restated Table I, so the shared "inherited from PGCF (Table I)" sentence now covers both. Saves a heading plus a partial line. |
| Results V-A | 151 → 126 | The ROC/PR sentence restated the AUC ordering already given in Table IV and described ROC curve shape in prose. The three Average Precision figures (0.9988 / 0.9841 / 0.9009) are new numbers and were kept. |
| Discussion VI-A | 163 → 132 | FPR-bound argument tightened; dropped the closing "trade-off to select deliberately based on the relative cost of false accusations versus missed detections" clause, which was a near-verbatim repeat of the paragraph closing Section III-C. |
| Limitations VI-B | 145 → 130 | Four bolded stand-alone paragraphs merged into one paragraph with run-in bold labels. All four limitations are still stated in full; this reclaims three partial end-of-paragraph lines. |

## Estimated total

**~0.3–0.35 pages.** This is a static estimate computed from word counts, figure aspect
ratios, and IEEEtran column geometry — see "Verification status" below.

In float-heavy IEEE papers the real gain is often somewhat larger than the sum of the
parts, because tightening the text lets a float that had been pushed to the following
page settle back onto the previous one.

## Verification status

**Not compile-verified.** Two reasons:

1. There is no LaTeX toolchain on the machine this pass was done on.
2. `figs/architecture.*` is referenced by `main.tex` but is not in the repo — only the
   10 `.jpg` result figures are. The paper therefore only builds in the Overleaf project
   where that file lives.

Confirm the page count by compiling on Overleaf.

## Remaining levers, if still over

In order of least damage:

1. `ablation_study.jpg` → `0.9\linewidth` (same 0.66 aspect ratio as `robustness_noise`,
   ~17 pt, zero content loss).
2. `robustness_noise.jpg` → `0.9\linewidth` (~17 pt).
3. Drop `ablation_study.jpg` entirely (~215 pt incl. caption). It plots AUC + accuracy
   for the four configurations; `metrics_unseen_forest.jpg` already plots *all five*
   metrics for the same four. This is the largest single remaining cut, and the two
   figures are genuinely redundant.
4. Drop Table II, the AND-gate truth table (~113 pt). Eq. (2) already states it
   exhaustively. Retained by explicit decision in this pass.

## Unused figures

These are in `figs/` but not referenced by the current `main.tex`, having been dropped
in an earlier trim: `calibration_curves.jpg`, `pr_curves.jpg`, `roc_curves.jpg`,
`confusion_matrices_indomain.jpg`, `metrics_indomain.jpg`. Their numbers are still cited
inline in the prose, which is fine — but note the abstract's stale "calibration curves"
mention, fixed in this pass, came from that earlier removal.
