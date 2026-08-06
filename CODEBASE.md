# Codebase Documentation

This file documents the source tree published under `github_codebase/`, which was
added to this repository in commit `9e53711` ("upload files"). Prior to that commit
the repository held only the paper drafts, figures and narrative notes; the actual
implementation lived outside version control. This document records what that upload
contains, so the code can be navigated without opening every file.

For the *methodology* narrative — why each framework exists and how it evolved —
see `research_paper_journey.txt`. This file covers *layout and artifacts*.

---

## 1. Top-level layout

```
github_codebase/
├── model.py                    PGCF architecture (visual stream)
├── loss.py                     PGCF multi-task loss
├── dataset.py                  Video dataset loaders, incl. PrecomputedTensorDataset
├── preprocess_dataset.py       Frame extraction / face cropping
├── build_combined_dataset.py   Merges Celeb-DF-v2 + FaceForensics++ into a balanced set
├── precompute_tensors.py       One-shot conversion of videos to .pt tensors
├── generate_graphs.py          Visual-model figure generation
├── utils.py                    Shared helpers
│
├── src/agcf/                   Audio-Guided Consistency Framework (audio stream)
├── src/fusion/                 Late-fusion logic gates
├── scripts/                    One-off analysis and figure scripts
│
├── figures/                    Single-modality (PGCF) figures
├── figures_fusion/             Multi-modal fusion figures
│
├── training.ipynb              Original PGCF training notebook
├── new_training.ipynb          Revamped pipeline using precomputed tensors
├── agcf_pipeline.ipynb         End-to-end audio pipeline
│
├── *_predictions.csv           Per-clip model outputs
└── fusion_comparison_results.csv   Headline metric table
```

Total: 46 tracked files, ~2,900 lines of Python plus three notebooks.

## 2. Visual stream (PGCF)

`model.py` (331 lines) defines the Physical-Guided Consistency Framework. Its loss,
in `loss.py`, is a three-term multi-task objective:

```
L = L_cls + alpha * L_consist + beta * L_rppg     (defaults: alpha=0.3, beta=0.1)
```

- `L_cls` — cross-entropy over the real/fake logits.
- `L_consist` — penalises low consistency scores on fakes and high scores on reals.
- `L_rppg` — MSE between the reconstructed and ground-truth CHROM (rPPG) signal.

The data path is the part that received the most engineering attention. On-the-fly
OpenCV resizing, DCT and CHROM extraction over 120,000+ frames per epoch was
starving the GPU, so `precompute_tensors.py` (140 lines) runs that work exactly once
and writes `.pt` tensors to disk; `PrecomputedTensorDataset` in `dataset.py` then
loads them directly. `build_combined_dataset.py` (213 lines) produces the balanced
3,780-video Celeb-DF-v2 + FaceForensics++ (C23) corpus described in the README.

## 3. Audio stream (AGCF)

`src/agcf/` holds the audio framework, deliberately decoupled from PGCF:

| File | Lines | Role |
|---|---|---|
| `extract_audio.py` | 95 | Pulls and resamples audio tracks from source video |
| `dataset.py` | 97 | Identity-disjoint loader for FakeAVCeleb |
| `model.py` | 124 | Dual-stream (log-mel spectrogram + raw waveform) network |
| `train.py` | 108 | Training loop |
| `eval.py` | 84 | Evaluation with globally unique clip identifiers |

The identity-disjoint split in `dataset.py` and the unique-key construction in
`eval.py` are the two data-integrity fixes described in Phase 3 of the journey
document; they are the reason the audio-only numbers are trustworthy rather than
inflated.

## 4. Fusion

`src/fusion/and_gate.py` is small enough to state completely. `fuse_predictions`
takes per-clip fake-probabilities from both models and supports two modes:

- **hard** — an AND gate. Each stream is thresholded at 0.5 and the results
  are combined with bitwise AND. The probability product is returned separately
  as an AUC proxy, since the discrete AND has no usable ranking.
- **soft** — the product t-norm `p_video * p_audio`, thresholded at 0.25
  (i.e. `0.5 * 0.5`). The threshold is a placeholder and is marked as tunable
  in the source.

`src/fusion/compare_eval.py` (58 lines) drives both modes and emits the comparison
table.

## 5. Committed result artifacts

`agcf_predictions.csv` and `pgcf_predictions.csv` each hold 200 per-clip rows with
columns `clip_id,label,p_fake`, sharing a common clip-id key so the fusion scripts
can join them.

`fusion_comparison_results.csv` is the headline table:

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| PGCF (Video Only) | 0.9597 | 0.8761 | 0.9900 | 0.9296 |
| AGCF (Audio Only) | 0.8925 | 0.7941 | 0.8100 | 0.8020 |
| Late Fusion (Hard AND) | 0.9462 | 0.9878 | 0.8100 | 0.8901 |
| Late Fusion (Soft Product) | 0.9758 | 0.9691 | 0.9400 | 0.9543 |

**Note on consistency with the paper.** These figures come from the 200-clip
evaluation committed here. They are not the same run as the Phase 4 numbers quoted
in `research_paper_journey.txt` (which report Hard AND at accuracy 0.9862 and
precision 1.0000). Both sets should not be cited interchangeably — whichever run
the paper uses, the CSV in this repository should be regenerated to match before
submission.

## 6. What is deliberately not tracked

`github_codebase/.gitignore` excludes the large artifacts: dataset folders
(`Combined-32frames/`, `Celeb-DF-v2/`, `FaceForensics/`), the tensor cache, and
`saved_models/`. That last rule means **`saved_models/agcf_best.pth` (21 MB) is
present on disk but not committed** — the trained audio weights are not reproducible
from this repository alone and must be regenerated via `src/agcf/train.py` or
obtained separately.

One tracked exception: `archive (1)/FakeAVCeleb_v1.2/.../meta_data.csv` (3.5 MB) is
committed, because the ignore rule intended to cover it is corrupted (see below).

## 7. Known defects in the tracked files

Two files have UTF-16 text appended into UTF-8 content, which renders as a space
between every character:

- `github_codebase/.gitignore`, lines 27–32 — the patterns for
  `FakeAVCeleb_v1.2/`, `archive/`, `archive (1)/`, `*.mp4` and `*.npy` are
  **inert**. Git does not match them, which is why the 3.5 MB metadata CSV above
  is tracked.
- `github_codebase/README.md`, lines 47–50 — the "AGCF and Late Fusion Module"
  section is unreadable.

Both were almost certainly produced by appending with PowerShell's default
UTF-16LE output redirection. Rewriting the affected lines as UTF-8 fixes both.
This has not been done here, as it is a content change beyond documenting the
upload.
