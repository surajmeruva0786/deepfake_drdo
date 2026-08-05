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

---

# Fifth pass — cross-reference audit

A full check of every figure, table, and citation in the paper. One real defect found
and fixed; everything else verified clean.

## Fixed: bibliography was not in first-citation order

**IEEE numbers references by order of first citation.** The bibliography was in an
arbitrary order, so **11 of 12 numbers were wrong**:

| # | Was | Should be (and now is) |
|---|---|---|
| 1 | tolosana | tolosana ✓ (only one that was right) |
| 2 | rossler | **prajwal** — Wav2Lip, cited in Intro ¶2 |
| 3 | frank | **khalid** — FakeAVCeleb, Intro ¶4 |
| 4 | li | **cai** — LAV-DF, contributions bullet 4 |
| 5 | ciftci | **rossler** |
| 6 | sabir | **frank** |
| 7 | dehaan | **li** |
| 8 | woo | **ciftci** |
| 9 | khalid | **jung** |
| 10 | cai | **sabir** |
| 11 | jung | **woo** |
| 12 | prajwal | **dehaan** |

The four Introduction/contribution citations had been scattered to positions 2, 9, 10 and
12 while Related Work occupied the low numbers. Reordering only — no entry added,
removed, or reworded, **no length change**.

## Verified clean

| Check | Result |
|---|---|
| Labels defined vs. referenced | 9 labels, all referenced at least once; no orphans |
| Undefined `\ref` | none |
| Duplicate labels | none |
| Bibitems vs. citations | 12 entries, all cited; no uncited, no undefined `\cite` |
| Duplicate bib keys | none |
| `\includegraphics` targets | 4 of 5 resolve in `figs/` (see caveat) |
| Hand-written `Section~` cross-refs | all 6 resolve to the intended subsection |
| Fig./Figure/Table style | already correct |

On the last one: IEEE uses "Fig." mid-sentence and spells out "Figure" at the start of a
sentence. The paper already did exactly that — `Fig.~\ref{fig:forest}` mid-sentence in
§V-A, `Figure~` at the head of §V-B, §V-C and §V-D and in §III-A. No change needed.

## Outstanding caveat

`\includegraphics{figs/architecture}` has **no matching file in this repo** and no file
extension. It presumably resolves in the Overleaf project. This has been true through
every pass and is the reason none of the page-count work here is compile-verified.
Worth committing the architecture figure to `figs/` so the repo builds standalone.

## Unreferenced files in `figs/`

Six files are no longer used by `main.tex`, accumulated across the trims:
`ablation_study.jpg` (pass 4), `calibration_curves.jpg`, `pr_curves.jpg`,
`roc_curves.jpg`, `confusion_matrices_indomain.jpg`, `metrics_indomain.jpg`. Harmless —
LaTeX ignores them — and kept deliberately in case any need to come back.

## Remaining levers, if still over

In order of least damage:

1. ~~Drop Table II, the AND-gate truth table (~113 pt).~~ **Withdrawn — see the twelfth
   pass.** The polarity fix made this table load-bearing rather than redundant.
2. Related Work (269 words) is the only prose block never trimmed.
3. `tsne.jpg` is short (0.296 aspect ratio, ~75 pt) but its §V-C paragraph could lose
   ~20 words.

**Deliberately avoided:** applying *et al.* to `tolosana`, `rossler`, `frank`, or
`sabir` would save ~4 more bib lines cheaply, but those have 5–6 authors, under IEEE's
six-name threshold, and some style checkers flag it. Only reach for these if
levers 1–3 are exhausted.

---

# Sixth pass — PGCF and AGCF as one proposed framework

The third pass removed the *words* that made PGCF read as prior work. It was not enough:
the paper still told a sequential story — PGCF exists, it has a weakness, we extend it.
Two deeper causes, neither fixable by word substitution.

## Cause 1: the narrative arc

Both the abstract and the Introduction **opened by developing PGCF**, then pivoted:

> "We first develop PGCF… **PGCF performs well, but** because it analyzes video only, it
> is structurally blind to audio-only attacks. **We therefore extend it into** PGCF+AGCF,
> a two-branch detector **whose second network**…"

That is a story about improving an existing system. Both now open by proposing
**PGCF+AGCF** as the contribution and introduce the branches as peers:

> "We propose PGCF+AGCF, an audio-visual deepfake detector built from **two networks
> introduced in this work**. The Physiology-Guided Consistency Framework (PGCF) examines
> video… The Audio-Guided Consistency Framework (AGCF) examines the speech track through
> a stream-for-stream counterpart…"

The video-only blindness argument is kept — it is the paper's motivation — but made
**symmetric**: a video-only detector misses lip-sync attacks, an audio-only detector
misses a silent face-swap, so neither covers the attack surface alone. Previously only
the video half of that argument was stated, which framed audio as the fix for a video
problem rather than as an equal half of the design.

## Cause 2: one-directional mirroring

Every statement of correspondence ran **one way** — AGCF mirrored, corresponded to, was
identical to, inherited from, or reused PGCF. Cumulatively that casts PGCF as the
original and AGCF as the derivative, which is precisely the impression to avoid.

| Was | Now |
|---|---|
| "AGCF is designed so that every architectural choice **in PGCF** has a direct audio counterpart" | "**The two branches** are designed so that every architectural choice in one has a direct counterpart in the other" |
| "the **identical** temporal pipeline **used by PGCF**" | "the three-stage temporal pipeline **shared by both branches**" |
| "Both CNN designs are **inherited directly from their PGCF counterparts**" | "Both CNN designs are **matched to** their video-branch counterparts" |
| Table I: "*identical*: TGF → …" | Table I: "*shared*: TGF → …" |
| "AGCF is trained… **matching PGCF's regime**" | "**Both branches share a single training regime**" |
| "trained with the same objective… **as PGCF**" | "…as **the video branch**" |
| Conclusion: "AGCF, **its** architectural mirror" | "PGCF for video and AGCF for audio, designed as architectural mirrors **of each other**" |
| "an audio companion network" (abstract, intro) | "two networks introduced in this work" |
| "built in two stages" (contributions) | "comprising two networks **proposed here**" |

## Cause 3: the outline contradicted the prose

PGCF was a **subsubsection inside System Overview** while AGCF had a full subsection. The
table of contents itself said video was background and audio was the contribution.

```
was                                  now
III-A  System Overview               III-A  System Overview
         (sss) Video Branch (PGCF)   III-B  PGCF: Physiology-Guided Consistency Framework
III-B  AGCF: …                       III-C  AGCF: Audio-Guided Consistency Framework
III-C  Late Fusion                   III-D  Late Fusion
```

This was also item 1 of the planned-additions list below, now **applied**.

Renumbering broke two hand-written cross-references, both updated: `Section~III-A` →
`III-B` (§IV-A Datasets) and `Section~III-C` → `III-D` (§III-A System Overview). All six
`Section~` references re-verified to resolve.

## Related Work

PGCF was being discussed among the prior art in the third person — "the DCT-based
features underlying **PGCF's** frequency stream", "**PGCF's** CHROM-based rPPG stream",
"**AGCF** deliberately departs… **reusing** a backbone identical to **PGCF's**". A
reader skimming Related Work would file both as existing systems. Now phrased as
**"our video branch's"** and **"our audio branch's"** throughout.

## Cause 4: the abstract's opening line (follow-up fix)

Caught on a re-read after the pass above. The very first sentence argued **only the audio
case**:

> "Not every deepfake is visible in the video itself: in some forgeries the picture
> remains entirely authentic and only the voice has been cloned, a case a detector
> examining pixels alone will always miss."

Every clause points one way — video is insufficient, audio is what is missing — so the
paper's opening line implied AGCF was the novelty before a single contribution was
stated. Now symmetric:

> "A deepfake can hide in either modality: some forgeries leave the picture authentic and
> clone only the voice, others leave the speech untouched and swap only the face. Neither
> pixels nor audio alone can settle whether a video is genuine."

Both branches are motivated equally from the first line. **+6 words.**

## Cost

**+22 words and one promoted heading, ~+38 pt.** No metric, figure, table, or reference
changed. This is the first pass in the series that *grew* the paper; it is covered
several times over by the Table II cut queued below.

---

# Seventh pass — AND-gate polarity

**This is a correctness fix, not an editorial one, and it leaves the paper with known
stale numbers. Read the "outstanding" section below before submitting.**

## The defect

The gate applied AND to the *fake* indicator: a clip was FAKE only if both branches said
fake. The truth table therefore mapped

| PGCF | AGCF | old verdict |
|---|---|---|
| Real | Fake | **Real** |
| Fake | Real | **Real** |

A cloned voice over authentic video is exactly `video=Real, audio=Fake`. The paper cites
that attack, by name, in the abstract, the Introduction and §VI-A as the blind spot that
justifies building an audio branch — and the fusion rule classified it as Real. The rule
structurally could not detect the attack class that motivates the whole framework.

## The fix

Reformulated on the **Real** decision, which preserves the "Hard AND-gate" name
throughout the title, contribution bullet 2 and §III-D:

```
r_v = 1[P(fake|video) <= tau_v],  r_a = 1[P(fake|audio) <= tau_a]
y_AND = REAL  iff  (r_v = 1 AND r_a = 1),  else FAKE
```

Unanimity is now required to **clear** a clip, not to condemn it. A detection in either
modality is sufficient to flag it. Behaviourally this is OR-over-fake, but stated as
consensus-for-Real it stays an AND-gate and reads as the safer design.

## What changed

| Location | Change |
|---|---|
| Eq. (2) + setup | Recast on `r_v`/`r_a`, the binarized Real decisions |
| Table II | Rows Real/Fake and Fake/Real now return **Fake** |
| §III-D rationale | Argued the gate "trades recall for precision"; now correctly argues the reverse, and shows both single-modality attacks being flagged |
| §VI-A bound | Claimed FPR ≤ min(FPR_v, FPR_a). Now a *miss-rate* bound, FNR ≤ min(FNR_v, FNR_a), with FPR bounded above by FPR_v + FPR_a |
| Abstract, Introduction | Rule description only |

**Net +77 words.**

## OUTSTANDING — stale numbers, deliberately left in place

Every Hard-fusion number in the paper was computed under the old rule and **must be
recomputed before submission**:

- Table IV, row "Late Fusion (Hard AND)": 0.838 / 1.000 / 0.673 / 0.805
- Abstract: "the Hard AND-gate 100% precision — zero false positives on real videos — at
  83.8% accuracy"
- Conclusion: "a conservative Hard AND-gate achieves perfect precision (zero false
  positives) at 83.8% accuracy"
- §V-A: "Both fusion strategies achieve perfect precision (1.000)…", "the Hard AND-gate
  is the more conservative of the two, forfeiting 19.6 recall points" — now
  definitionally backwards; rewrite this paragraph wholesale after recomputing
- §V-B: "Both fusion rules inherit this conservatism (32 missed fakes under Hard AND)"
- `figs/confusion_matrices_unseen.jpg`: the Hard AND panel
- `figs/metrics_unseen_forest.jpg`: the Hard AND bars

**Perfect precision will not survive.** On the prediction CSVs in `github_codebase/`
(a 168-clip set, 100 fake / 68 real, which does *not* match the paper's n=198 — PGCF's
precision/recall/F1 match the paper exactly but AGCF's and Soft's do not):

| Rule | Acc | Prec | Rec | F1 | TP/FP/FN/TN |
|---|---|---|---|---|---|
| Old (AND on fake) | 0.881 | 0.988 | 0.810 | 0.890 | 81/1/19/67 |
| **New (AND on real)** | **0.946** | **0.925** | **0.990** | **0.957** | 99/8/1/60 |

Better on accuracy and F1 — it stops the audio branch vetoing 18 correct video
detections — but precision falls from 0.988 to 0.925.

## Two related issues found, not changed

1. **The Soft rule has the same defect.** `P_fused = P(fake|video) × P(fake|audio)` is
   the soft analogue of AND-on-fake: a confident audio detection multiplied by a low
   video score still yields a low fused score, so single-modality attacks are suppressed.
   The noisy-OR form `1 − (1−P_v)(1−P_a)` would be the counterpart of the corrected hard
   rule. Left alone because changing it invalidates the Soft numbers too.

2. **"AGCF catches the audio-only attacks PGCF cannot" may be unsupported.** In the
   prediction data, among 100 true fakes, the number detected by audio alone is **zero** —
   all of the corrected gate's extra detections come from video-only cases. If that holds
   on the real evaluation set, this claim (abstract, Introduction, §VI-A) is theoretical
   rather than demonstrated, and a reviewer could challenge it.

---

# Eighth pass — LAV-DF moved from claimed work to future work

**A second correctness fix.** The paper claimed an LAV-DF cross-dataset pipeline as a
*delivered engineering contribution*, with only the numbers outstanding:

> "We built an auto-resuming extraction pipeline for the 23.1 GB archive, a balanced
> 150-real/150-fake filtration script, and a zero-shot cross-evaluation script; the
> numerical results were not finalized in time for this submission and are reported as
> ongoing work rather than estimated."

No LAV-DF work was done. The dataset is a future intention. Claiming a built pipeline —
with specific artefacts and file sizes — is the kind of detail a reviewer may ask to see.

## Changes

| Location | Was | Now |
|---|---|---|
| Contributions, bullet 4 | "…plus a complete code-level pipeline for **cross-dataset generalization** testing on LAV-DF, contributed as engineering work with results reported as ongoing rather than estimated" | Clause removed. Bullet claims only the evaluation suite that exists. |
| §IV-A Datasets | A full LAV-DF paragraph describing the extractor, filtration script and cross-eval driver | **Paragraph deleted.** Datasets now lists the two corpora actually used: Celeb-DF-v2 and FakeAVCeleb. |
| Related Work | "FakeAVCeleb and LAV-DF … are the datasets **used here** for audio-branch training/validation and cross-dataset generalization testing, respectively" | "FakeAVCeleb is the corpus used in this work, and LAV-DF is the natural target for the cross-dataset evaluation **we leave to future work**" |
| Conclusion | "completing the cross-dataset LAV-DF evaluation **begun in this work**" | "a zero-shot cross-dataset evaluation on LAV-DF" |
| §VI-B Limitations | "broader validation, alongside the LAV-DF cross-dataset evaluation, remains future work" | Unchanged — already correctly future-framed |

All three surviving LAV-DF mentions are now unambiguously forward-looking.

## Knock-on: bibliography reordered again

Dropping the citation from contributions bullet 4 moved `cai2022lavdf`'s first mention
from position 4 to position 10, breaking IEEE first-citation numbering. Reordered to:
tolosana, prajwal, khalid, rossler, frank, li, ciftci, jung, sabir, **cai**, woo, dehaan.
Audit re-run clean — no orphan labels, no undefined or uncited references.

## Cost

**−63 words (~73 pt).** This offsets the seventh pass's +77 words almost exactly, so the
two correctness passes together are close to length-neutral.

---

# Ninth pass — dataset table and Future Work section (planned items 2 and 3, APPLIED)

All three planned additions are now in the paper. Item 1 (PGCF subsection) landed in the
sixth pass; items 2 and 3 are described here.

## Dataset table (§IV-A)

Replaces the two remaining descriptive paragraphs. **The corpus figures were recovered
from the repository, not estimated** — the plan had flagged them as blocked, but
`github_codebase/` turned out to contain the sources:

| Source | Yielded |
|---|---|
| `archive (1)/…/meta_data.csv` | FakeAVCeleb: 21,566 clips, 500 subjects, five ethnicities, both genders; 500 RealVideo-RealAudio; methods wav2lip (9,602), fsgan (3,964), fsgan-wav2lip (3,553), faceswap-wav2lip (2,717), faceswap (730), rtvc (500) |
| `build_combined_dataset.py` | Celeb-DF-v2: 590 real (Celeb-real) / 5,639 fake (Celeb-synthesis) |
| `dataset.py` | Celeb-DF-v2 split `val_ratio=0.2` → 80/20, balanced |
| the paper itself | FakeAVCeleb held-out: 198 clips (100 real / 98 fake), subject-level |

No cell is invented. The **LAV-DF row from the planned table was dropped** — the eighth
pass established that dataset was never used, so it cannot appear in a table of corpora
used.

Kept as prose because it is not tabular: the caveat that PGCF is scored on FakeAVCeleb
partitions for protocol parity, *not* as a replacement for its Celeb-DF-v2 result.
Preprocessing (T=16, 16 kHz, 1 s windows, 64 mel bins) moved into the lead-in sentence.

Table count is now **five**: mirror, truth, **datasets**, leakage, main.

## Future Work (§VI-C)

Written as a *consolidation*, as planned. Each of the four limitations maps to exactly
one direction, and **every forward-looking clause was removed from Limitations** so
nothing is stated twice:

| Clause | Was in | Now in |
|---|---|---|
| "stronger audio-specific backbones… could narrow this gap" | VI-B | VI-C only |
| "post-hoc temperature scaling is recommended" | VI-B | VI-C only |
| "a threshold search would likely improve the balance" | VI-B | VI-C only |
| "broader validation… remains future work" | VI-B | VI-C only |
| "Future work will focus on…" (whole sentence) | Conclusion | **deleted** |

Limitations now states only limitations. The Conclusion now ends on the
evaluation-integrity finding. VI-C adds one direction the paper had not previously
raised — feature-level rather than decision-level fusion, which the shared temporal
pipeline already makes feasible.

Placed before the Conclusion, per IEEE convention that nothing follows it but
Acknowledgment and Appendix.

## Cost — higher than planned

**+48 words, one table, one heading: ~+220 pt (~0.33 column), against a planned +16 pt.**

The plan costed the dataset table as *net −45 pt* on the assumption it would displace 136
words of §IV-A prose. The eighth pass had already deleted the LAV-DF paragraph, leaving
only ~88 words for the table to absorb, so the displacement saving mostly evaporated. The
Future Work consolidation came in near its +61 pt estimate.

**Recommendation (withdrawn):** this originally proposed cutting Table II (~113 pt) to
offset half the growth, on the grounds that after the polarity fix the table "has three
identical Fake rows and carries even less information than before". That reasoning was
backwards and is retracted in the twelfth pass — those three rows are exactly what a
reader needs in order to understand the corrected rule.

## Noted, not fixed

**Celeb-DF-v2 is used but never cited.** It appears in the abstract, Introduction, §IV-A
and the new table with no `\cite`. A reviewer may flag using a dataset without citing it.
Adding the reference costs ~3 bibliography lines (~29 pt); left to the authors given the
page pressure.

---

# Tenth pass — abstract condensed and made coherent

The abstract had grown to **303 words**, over the 250-word limit, and read as a list of
facts rather than a single argument. Now **240 words, 9 sentences**.

## Coherence

The clearest defect was that it made the same point twice:

- sentence 2 — "Neither pixels nor audio alone can settle whether a video is genuine"
- sentence 7 — "Neither modality covers the attack surface alone"

The second is gone. The remaining sentences now hand off to one another in a single arc —
problem → proposal → PGCF → AGCF → why the mirroring matters → fusion → results → audit —
rather than restarting at each new topic. The connective tissue is explicit
("therefore", "Because the two branches are…", "An audit of our own protocol then…").

## Readability

Removed architecture detail that belongs in Table I and §III, not an abstract:
`Classifier(512→2)`, the `4-head` and `(256)` sizings, and the stream-by-stream pairing
of the spectral CNN to the DCT stream and the waveform CNN to the rPPG stream. AGCF is
now introduced as applying "the same principle to speech", which is the idea a reader
needs at this point.

The trailing sentence — "Robustness under additive Gaussian noise, ROC/PR analysis, and
t-SNE feature-space visualization are reported for all four configurations" — was an
inventory bolted onto the end. The parts worth keeping are folded into the results
sentence.

## One correctness side effect

The Hard AND-gate's headline figure — "100% precision — zero false positives on real
videos — at 83.8% accuracy" — was **dropped**. It was computed under the old gate
polarity (seventh pass) and will not survive recomputation, so removing it during a
condensation pass avoids asserting a number known to be wrong. The *rule* is still
described in the abstract; only its stale result is gone.

This shortens the outstanding-stale-numbers list from the seventh pass by one item. The
remainder still stand: Table V row 4, the Conclusion's claim, and §V-A/§V-B.

## Cost

**−63 words (~73 pt)**, offsetting about a third of the ninth pass's growth.

---

# Eleventh pass — claims about figures that are not in the paper

ROC curves, PR curves and calibration curves were removed from the paper in earlier
trims, but four passages still described them. **No `\ref` was broken** — every one of
these was plain prose, which is why the cross-reference audit never flagged them and why
they survived ten passes.

| Location | Was | Now |
|---|---|---|
| Contributions, bullet 4 | "**ROC/PR analysis**, confusion matrices, t-SNE visualization, and Gaussian-noise robustness" — the other three have figures; ROC/PR does not | "AUC and average-precision scores, confusion matrices, …" |
| §V-A | "AGCF's 0.9009 **degrades further beyond a recall of roughly 0.5**" — a description of a PR curve's shape | Curve-shape clause dropped; the three AP scalars stand alone |
| §VI-B Calibration | "PGCF and AGCF are both under-confident **below a predicted probability of 0.6**" — a value read off a reliability diagram | States the calibration limitation without the unverifiable threshold |
| §III-D Soft rule | "a soft, probabilistic score suitable for **ROC/PR analysis**" | "a rankable score suitable for AUC and average-precision analysis" |

Left unchanged: §III-D's "excluded from ROC/PR/AUC analysis, which requires a rankable
score" (explains the "—" in Table V, does not promise a figure) and the noise figure's
"AUC-ROC under increasing additive Gaussian noise" caption (that figure exists and plots
AUC values).

## Why not just add the figures back

`calibration_curves.jpg`, `pr_curves.jpg` and `roc_curves.jpg` are all still in `figs/`.
Restoring all three costs roughly **660 pt — a full page** at 0.873 aspect ratio plus
captions. Not viable against a 6-page limit. Aligning the claims with what is shown costs
nothing and saves 23 words.

## Cost

**−23 words.**

## Still-unreferenced files in `figs/`

`ablation_study.jpg`, `calibration_curves.jpg`, `pr_curves.jpg`, `roc_curves.jpg`,
`confusion_matrices_indomain.jpg`, `metrics_indomain.jpg`. Harmless — LaTeX ignores
them — and no prose now claims any of them.

---

# Twelfth pass — Table II kept and disambiguated (recommendation retracted)

## Retraction

Earlier passes recommended cutting Table II (the AND-gate truth table) **nine times**
across this document, after the authors had already declined twice. The recommendation is
**withdrawn**, and not only because it was over-repeated: the reasoning stopped being
correct at the seventh pass.

The original case was sound — a four-row truth table for a two-input boolean gate is
redundant against Eq. (2), and at ~113 pt it was the largest lossless cut available. But
the polarity fix changed what the table is *for*. "Hard AND-gate" now denotes AND over
the **Real** decisions, which is not the reading a reviewer will assume. The truth table
is the fastest way to convey that. The ninth pass argued the opposite — that three
identical "Fake" rows meant it "carries even less information than before" — which is
backwards: those three rows are the entire point of the corrected rule.

## The real problem, which is labelling not redundancy

Captioned "Hard AND-Gate Fusion Truth Table" and showing Fake in three of four rows, the
table depicts — under the conventional Fake = 1 encoding a reader carries in — the truth
table of an **OR** gate. The resolution is in Eq. (2) and the surrounding prose, but
tables are read out of order and this one did not stand on its own.

Fixed by making it self-contained rather than by deleting it:

- **Added an $r_v \wedge r_a$ column** showing 1, 0, 0, 0 — the AND is now literally
  visible, and it is immediately clear what the AND is over.
- **Caption now states the semantics**: "The AND is taken over the *Real* decisions
  $r_v, r_a$, so unanimity clears a clip and a detection in either modality alone yields
  FAKE."

Cost: one extra narrow column and roughly one caption line, ~10 pt.

## Note on the levers generally

Every space lever proposed in this document has been sized from static estimates —
word counts, figure aspect ratios and IEEEtran column geometry. **No pass has ever been
verified against a real compile**, because there is no TeX toolchain here and
`figs/architecture` is not in the repo. That is why cuts kept being proposed from a
generic list rather than against a measured shortfall.

---

# Thirteenth pass — T standardized, Celeb-DF-v2 cited

Two fixes from the final line-by-line review.

## T=16 vs T=32

The clip length was stated three different ways:

| Location | Was |
|---|---|
| §III-B (PGCF) | `T=32` frames per clip |
| §III-C (audio windowing) | "the same `T=16` chunks used for video" |
| §IV-A (preprocessing) | "Video is sampled at `T=16` frames per clip" |

**Standardized on T=32**, per the authors, which also matches the repo's
`Celeb-DF-v2-32frames` and `Combined-32frames` directories.

**Open arithmetic question, not resolved here:** §III-C describes each audio chunk as a
one-second, 16,000-sample waveform. At T=32 chunks that implies 32 s of audio per clip,
which is far longer than a typical FakeAVCeleb clip. Either the chunks are shorter than
1 s, or they overlap, or the audio branch uses a different T from the video branch. Worth
checking before submission — a reviewer who multiplies these two numbers will notice.

## Celeb-DF-v2 citation

The corpus is used in the abstract, the Introduction, §IV-A and the dataset table, and
was **never cited**. Added:

> Y. Li, X. Yang, P. Sun, H. Qi, and S. Lyu, "Celeb-DF: A large-scale challenging dataset
> for DeepFake forensics," *Proc. IEEE/CVF CVPR*, 2020, pp. 3207–3216.

Cited at first mention (Introduction ¶2) and in the dataset table header, matching how
FakeAVCeleb is handled. Note this is a *different* paper from the existing
`li2019exposing` (X. Li and S. Lyu, face-warping artifacts), hence the separate key
`li2020celebdf`.

**Bibliography renumbered again** — the new entry takes position 2 by first-citation
order: tolosana, **celebdf**, prajwal, khalid, rossler, frank, li2019, ciftci, jung,
sabir, cai, woo, dehaan. Now 13 references. Audit clean.

Cost: ~+29 pt for the extra bibliography entry.

## Still outstanding from the final review

Not addressed in this pass, listed here so they are not lost:

1. **Hard-fusion numbers are stale** (Table V row 4, §V-A, §V-B, confusion-matrix
   figure). §V-A's "the Hard AND-gate is the more conservative of the two" is now
   backwards. Bounds derived from Table V and the §V-B confusion counts:
   accuracy 0.929–0.944, precision 0.882–0.899, recall 0.990–1.000.
2. **PGCF's training corpus may be undisclosed.** `build_combined_dataset.py` assembles
   Celeb-DF-v2 *plus 7,000 FaceForensics++ folders*; the paper says Celeb-DF-v2 only.
   Needs the authors to confirm which was actually used.
3. **PGCF's 0.999 AUC reads as a cross-dataset result** (trained per the paper on
   Celeb-DF-v2, evaluated on FakeAVCeleb) that exceeds published state of the art, in a
   paper that calls cross-dataset evaluation future work.
4. **`figs/architecture` is not in the repo** — the paper does not compile standalone.
5. **The Soft rule retains the old polarity**, suppressing exactly the single-modality
   attacks the corrected Hard gate catches. The two rules now embody opposite
   philosophies without the paper acknowledging it.
6. **No baseline comparison** against any published method on the paper's own split.

---

# Fourteenth pass — venue fit for WiCOMM-2026 (DRDO)

Target venue: International Conference on Wireless Communication for Military
Applications, WiCOMM-2026, DRDO-conducted.

## Scope caveat, recorded up front

**The paper contains no wireless content** — no channel model, link budget, protocol,
spectrum or physical-layer work. Four sentences do not change that, and a scope
desk-reject remains the realistic risk. These additions reduce it; they do not remove it.
The genuine bridge is §V-D, the noise-robustness sweep, and everything below leans on it.

## What was added

| Location | Addition | Words |
|---|---|---|
| Introduction ¶1 | One sentence placing deepfakes in defence communications — a cloned voice on a command channel, a manipulated video briefing acted on before it can be authenticated. Placed *inside* the existing motivation, not appended after it. | ~30 |
| §V-D | The closing clause now draws a conclusion from the noise data rather than gesturing at it: the audio branch degrades first, so the video branch should carry proportionally more weight as channel quality falls, and a fixed product rule is wrong for a link whose SNR varies. | ~45 |
| §VI-A | In a monitoring role, where flagged material is escalated to a human analyst rather than acted on automatically, the precision/recall balance favours recall — the regime the corrected AND-gate occupies. | ~30 |
| §VI-C | A deployment direction (below). | ~62 |

**+116 words, ~134 pt.**

## The deployment sentence, and why it is not the one requested

The request was to state that the model is small, easily deployable, and usable for
real-time wireless deepfake detection. Written that way it would be **unsupported and
checkable**: `model.py` shows PGCF's spatial stream is a full **ResNet50** (~23.5M
parameters, ~94 MB in fp32), which is not small by edge standards, and the paper reports
no latency or memory figures at all. A defence audience evaluating deployability is
exactly the audience that would verify this.

What went in instead makes the same case defensibly:

> "AGCF is compact — two three-layer CNNs over the shared temporal head — while PGCF's
> footprint is dominated by its ResNet50 spatial stream, so substituting a mobile-class
> backbone would bring the pair within reach of on-device inference. The target is
> real-time screening of audio-visual traffic at a communications endpoint, contingent on
> the latency and memory characterization we have not yet carried out."

This names the actual bottleneck and a concrete engineering step, which reads as
engineering judgement rather than an adjective, and it cannot be falsified by a reviewer
who counts parameters.

## Deliberately not done

- **Title unchanged.** "…for Defence Applications" would read as exactly the
  advertisement the authors wanted to avoid, and invites "generic deepfake paper with a
  label attached".
- **No "Military Applications" subsection.** Reviewers discount these.
- **Abstract untouched.** At 240 of 250 words it is the most expensive place to add and
  the most visible bolt-on; the Introduction does the same work one paragraph later.
- **Keywords unchanged**, by author decision.

## The change that would actually establish venue fit

Not a sentence. Re-run the §V-D sweep against a **channel** rather than an abstract
$\sigma$: AWGN at stated SNRs, or codec degradation at tactical bitrates (AMR-NB, Opus at
low rate). Same experiment, same figure, but the x-axis becomes something a wireless
audience recognises, and the paper stops being an AV-forensics paper wearing a defence
label. This would do more for acceptance at WiCOMM than every sentence above combined.

---

# PLANNED — all items applied

Three changes proposed by the authors, costed against the page budget. **Net cost of all
three is ~+24 pt**, because two of them are restructurings rather than additions.
Cutting Table II alone more than pays for them.

## 1. Promote PGCF to its own subsection

```
III-A  System Overview
III-B  PGCF: Physiology-Guided Consistency Framework   <- promoted from subsubsection
III-C  AGCF: Audio-Guided Consistency Framework
III-D  Late Fusion: Soft vs. Hard AND-Gate
```

Today AGCF has a full subsection while PGCF sits one level deeper, inside "System
Overview". The outline therefore *still* says what the third pass removed from the
prose — that video is background and audio is the contribution. **~+8 pt.**

Knock-on: renumbering breaks two hand-written cross-references —
`Section~III-A` → `III-B` in §IV-A Datasets, and `Section~III-C` → `III-D` in System
Overview. The audit script (`labels/refs` + `Section~` resolution) catches these.

## 2. Dataset table, replacing the §IV-A prose

A reproducibility table, **replacing** the three descriptive paragraphs rather than
sitting alongside them — that prose is exactly what belongs in a table.

| Dataset | Role here | Clips (real/fake) | Subjects | Split | Manipulations |
|---|---|---|---|---|---|
| Celeb-DF-v2 | Train/val PGCF | ? | ? | ? | face-swap |
| FakeAVCeleb | Train/val AGCF; fusion eval | 198 (100/98) eval | ? | identity-disjoint | FaceSwap, Wav2Lip, DeepFaceLab |
| LAV-DF | Cross-dataset (ongoing) | 300 (150/150) | ? | zero-shot | content-driven A/V |

Remove 136 words (−195 pt), add table (~105 pt) + two-sentence lead-in (~46 pt) =
**net −45 pt.** Frees space *and* serves reproducibility better than the prose.

**Blocked on numbers not present anywhere in the paper:** Celeb-DF-v2 clip counts,
real/fake split, subject count and train/val partition (the only Celeb-DF-v2 figure in
the paper is AUC 0.824); FakeAVCeleb *training* clip and subject counts (only evaluation
splits are given); LAV-DF subject count. Preprocessing can be filled from the paper
already: T=16 frames, 16 kHz, 1 s / 16,000-sample windows, 64 mel bins. Unknown cells
should be "—" rather than invented.

Table count stays at four: mirror, **dataset**, leakage, main.

## 3. Future work as §VI-C, consolidating rather than adding

The authors asked for a future-directions section. Future work is currently stated in
**two** places already — the Conclusion's closing sentence, and a forward-looking clause
in all four Limitations entries. A third location would be visible padding.

Instead, `VI-C` **absorbs** both: Limitations then states limitations, the Conclusion
concludes, and future work gets one home with room to say more than one sentence.

Placed as a Discussion subsection, not a section after the Conclusion — IEEE convention
is that nothing follows the Conclusion but Acknowledgment and Appendix.

~120 new words (+138 pt) + heading (+15 pt), less ~45 words from Limitations (−52 pt)
and ~35 words from the Conclusion (−40 pt) = **~+61 pt**, against ~150 pt if appended.

**Care needed:** some Limitations clauses are load-bearing for the limitation itself,
not merely forward-looking ("stronger backbones could narrow this gap" explains *why*
the gap is addressable). Better to leave such a clause in place and absorb the ~20 pt
than to leave a stub.

## Budget

| Item | pt |
|---|---|
| PGCF promotion | +8 |
| Dataset table (replacing prose) | −45 |
| Future work §VI-C (consolidating) | +61 |
| **Net cost of all three** | **+24** |
| Cut Table II | −113 |
| **Net** | **−89** |

## Explicitly kept

Sized against these *restructured* proposals, the t-SNE figure does **not** need to go —
it is worth more than a truth table restating Eq. (2). Related Work and §VI-A stay
untouched. Table III and §IV-B (the evaluation-integrity audit) are the most distinctive
material in the paper and were never cut candidates.

## Unused figures

These are in `figs/` but not referenced by the current `main.tex`, having been dropped
in an earlier trim: `calibration_curves.jpg`, `pr_curves.jpg`, `roc_curves.jpg`,
`confusion_matrices_indomain.jpg`, `metrics_indomain.jpg`. Their numbers are still cited
inline in the prose, which is fine — but note the abstract's stale "calibration curves"
mention, fixed in this pass, came from that earlier removal.
