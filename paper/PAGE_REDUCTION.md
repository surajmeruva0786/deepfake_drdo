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

---

# Second pass — closing the last two reference lines

After compiling pass 1 on Overleaf, **two reference entries** still sat on page 7.
That is a gap of roughly **55–70 pt** of a single column (the bibliography runs at 8 pt,
~9.7 pt per line, and the 12 entries occupied ~38 lines ≈ 369 pt).

Four bib entries happened to sit *just past* a line boundary, wasting most of a line
each, which made this cheap to close.

| Change | Est. reclaimed |
|---|---|
| `\itemsep`/`\parsep` zeroed inside `thebibliography` (12 entries) | ~15–25 pt |
| `cai2022lavdf`: venue → `Proc. DICTA` | ~10 pt (5 → 4 lines) |
| `jung2022aasist`: → `J. Jung et al.` | ~10 pt (4 → 3 lines) |
| `ablation_study.jpg` → `0.9\linewidth` | ~17 pt |
| `robustness_noise.jpg` → `0.9\linewidth` | ~17 pt |

**Total ~68–78 pt**, against a 55–70 pt gap. Bibliography went from ~38 to ~36 lines.

Two notes on the bibliography edits:

- The DICTA entry was **one character** past a 5-line boundary. Abbreviating
  `2022 Int. Conf. Digital Image Computing: Techniques and Applications (DICTA)` to
  `Proc. DICTA` is standard IEEE venue abbreviation — no information lost.
- `jung2022aasist` has **eight** authors. IEEE style is to use *et al.* past six names,
  so `J. Jung et al.` is a style-compliance fix that happens to save a line, not a
  corner cut under page pressure.

---

# Third pass — authorship framing, retitle, and the last reference line

Two problems addressed together, because the fix for one paid for the other.

## The framing problem

The paper read as though **PGCF was pre-existing work** that this paper merely bolted
an audio branch onto. That is wrong: both branches are ours. Video was stage one of the
project, audio was added second, and the proposed contribution is the combined
two-branch system.

The clearest symptom: **the contributions list never claimed PGCF at all.** Bullet 1
described AGCF only, so a reader would reasonably infer the video model came from
somewhere else. Seven passages contributed to the impression:

| Location | Was | Now |
|---|---|---|
| Contributions, bullet 1 | "**AGCF**, a dual-stream audio deepfake detector…" | "**PGCF+AGCF**, a two-branch audio-visual detector built in two stages…" |
| Abstract | "an audio companion network" | "extend it into PGCF+AGCF, a two-branch detector whose second network…" |
| Introduction ¶3 | "an audio companion network designed as a mirror of PGCF" | "extend PGCF into the two-branch PGCF+AGCF framework by developing a second network" |
| §III-A heading | "PGCF Recap" | "Video Branch (PGCF)", + "the first stage of this work" |
| §III-A close | "PGCF is not modified in this work." | *removed* |
| §III-C open | "trained independently, which keeps PGCF completely unmodified" | "trained independently" |
| §III (System Overview) | "PGCF is used exactly as developed in Section III-A" | *removed* |
| §IV-A Datasets | "the visual-only PGCF **baseline**" | "the **video branch**, PGCF" |
| Conclusion | "We presented **AGCF**, an audio companion network…" | "We presented **PGCF+AGCF**, a two-branch detector developed in two stages…" |

"Recap", "baseline", "not modified", "companion" and "used exactly as developed" are all
words that signal *someone else's finished artifact*. None of them survive.

## Title

| | |
|---|---|
| Pass 1 | PGCF+AGCF: Physiology- and Audio-Guided Consistency for Multi-Modal Deepfake Detection |
| Interim | PGCF+AGCF: Physiology- and Audio-Guided Consistency for Audio-Visual Deepfake Detection |
| **Final** | **PGCF+AGCF: Physiology-Guided Video and Audio-Guided Consistency for Deepfake Detection** |

Three changes, one line of reasoning each:

- **"Video" is now named.** The old title said "Audio-Guided" and "AGCF" but never
  identified the visual modality — "Multi-Modal" was carrying that implicitly. Since the
  video branch is half the contribution, it gets named.
- **The suspended hyphen is gone.** "Physiology- and Audio-Guided" was correct English
  (the trailing hyphen elides a shared "Guided", as in "pre- and post-processing"), but
  spelling both out reads plainer and lets "Video" slot in naturally.
- **"Multi-Modal"/"Audio-Visual" dropped.** With *Video* and *Audio* both named in the
  title, it was redundant. Dropping it keeps the title at 86 characters — **still two
  lines at IEEEtran title size, so the retitle costs no page space.**

## Closing the last reference line

After pass 2, **one** reference entry still sat on page 7 — roughly 20–30 pt.

The framing rewrite was deliberately built to be *net-negative* in length so it could pay
for this itself. The claim-strengthening edits (contributions bullet, Conclusion) added
~20 words; the de-hedging edits (removing "not modified", "unmodified", "exactly as
developed", "exclusively", "baseline") removed ~30. That netted only −10, so two further
trims were added:

| Change | Words |
|---|---|
| §IV-A LAV-DF paragraph — the reserved "Tier B" trim | −17 |
| §IV-B paragraph after Table III — hedging around the PGCF split comparison | −17 |
| Caption skip 3 pt → 2 pt across 6 figures + 4 tables | ~10 pt |

**Net −26 words (~38 pt) plus ~10 pt of caption skip**, against a 20–30 pt gap.

---

# Fourth pass — drop the ablation figure

Pass 3 did not clear page 7. Taking the largest lever off the reserve list.

## What changed

`figs/ablation_study.jpg` and its float are **removed**. It plotted AUC-ROC and accuracy
for the four configurations; `metrics_unseen_forest.jpg` already plots **all five**
metrics for the same four configurations, so the ablation figure was a strict subset of
the forest plot. Nothing is shown in the paper that was only shown there.

| | |
|---|---|
| Figure + caption + float separation | **~170 pt** freed |
| Longer forest caption (1 line → ~3) | −19 pt |
| §V-A sentence reworked (−6 words) | −7 pt |
| **Net** | **~158 pt (~0.24 column)** |

The paper is now **5 figures**: architecture, forest, confusion matrices, t-SNE, noise
robustness.

## Keeping the ablation framing

Dropping the figure must not drop the *claim* — "ablation study" is how reviewers look
for per-modality contribution analysis, and the paper should still visibly do one. Two
edits preserve it:

- The forest plot's caption is retitled **"Ablation study: per-metric comparison across
  all four configurations… isolating the contribution of each modality and of each
  fusion rule."** It also now states that the Hard AND-gate has no AUC bar because it
  produces no rankable score — a point the deleted caption had been carrying.
- The §V-A sentence that pointed at both figures now points at the forest plot alone and
  names it as the ablation.

`figs/ablation_study.jpg` is left in the repo, unreferenced, alongside the other five
figures dropped in earlier trims.

## Remaining levers, if still over

In order of least damage:

1. Drop Table II, the AND-gate truth table (~113 pt). Eq. (2) already states it
   exhaustively. Retained by explicit decision in all four passes.
2. Related Work (269 words) is the only prose block never trimmed.
3. `tsne.jpg` is short (0.296 aspect ratio, ~75 pt) but its §V-C paragraph could lose
   ~20 words.

**Deliberately avoided:** applying *et al.* to `tolosana`, `rossler`, `frank`, or
`sabir` would save ~4 more bib lines cheaply, but those have 5–6 authors, under IEEE's
six-name threshold, and some style checkers flag it. Only reach for these if
levers 1–3 are exhausted.

## Unused figures

These are in `figs/` but not referenced by the current `main.tex`, having been dropped
in an earlier trim: `calibration_curves.jpg`, `pr_curves.jpg`, `roc_curves.jpg`,
`confusion_matrices_indomain.jpg`, `metrics_indomain.jpg`. Their numbers are still cited
inline in the prose, which is fine — but note the abstract's stale "calibration curves"
mention, fixed in this pass, came from that earlier removal.
