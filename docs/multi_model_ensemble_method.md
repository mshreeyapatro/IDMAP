# Multi-Model TCIR Pretraining with a Learned Combiner

Reference document for the mentor-directed Phase 3 variant. Companion to
`docs/dataset_audit_report.md` (Phase 1) and the project's SRS PDF (sections
5–6, "Multi-Model Satellite Vision Architecture" / "GPU-/Compute Strategy").

## 1. What was asked for, in plain terms

> Take ~10,000 images, split them into subsets of ~1,000, train a separate
> model on each subset, then combine those models with another model that
> gets used downstream — all with low/no GPU usage.

This is not a new idea layered onto the project: it is the architecture the
project's own SRS document already specifies in sections 5 and 6, described
there but never actually built. What existed before this change was a
simplification of that plan — one model, trained on one 6,000-image random
subset. This document describes building the SRS's original multi-model
design for real, evaluating it against that simplification, and being
explicit about where the two differ from the most literal reading of the
mentor's instruction.

## 2. Why insat3d couldn't be the dataset for this

The Odisha-tagged dataset (`data/raw/insat3d/`) has ~140 raw images across 66
storm events (see `docs/dataset_audit_report.md` and
`data/processed/insat3d_event_identity.csv`) — nowhere near 10,000, and far
too small to split into ten 1,000-image subsets. Splitting it that way was
never going to work regardless of implementation effort; the data simply
isn't there.

**TCIR** (`data/raw/tcir_global/images.h5`) is: 21,076 labeled global cyclone
images (128×128, 4 channels, real Vmax/MSLP labels), already in the project
and already scoped as a pretraining-only source (never mixed into Odisha
event splits — see the TCIR scope decision). It's the dataset this method
runs on. insat3d's role is unchanged: it's still what the trained
backbone/ensemble extracts features *from* for the actual Odisha risk
pipeline (`src/cv_models/extract_insat3d_features.py`), not what gets split
into training subsets.

## 3. Architecture

```
TCIR pool (21,076 images)
        │
        ├── 10,000 images → 10 subsets of 1,000
        │         │
        │         ├── Subset 1 → load → train TinyCNN #1 → checkpoint → release
        │         ├── Subset 2 → load → train TinyCNN #2 → checkpoint → release
        │         │        ⋮                                          (sequential —
        │         └── Subset 10 → load → train TinyCNN #10 → checkpoint → release   never more than
        │                                                                            1 model + 1 subset
        │                                                                            in memory at once)
        ├── 2,000 images → combiner training set
        │         │
        │         └── frozen embeddings from all 10 sub-models, concatenated (10×32 = 320-dim)
        │                       │
        │                       └── CombinerNet (small MLP, trained on Vmax) → combined 32-dim embedding
        │
        └── 2,000 images → held-out test set (unseen by every sub-model AND the combiner)
                  │
                  └── used ONLY for the single-backbone vs. ensemble comparison below
```

Each sub-model (`TinyCNN`, `src/cv_models/backbone.py`) is the same small
4-layer CNN already used for the original single backbone — 3 conv blocks +
global pooling + a 32-dim embedding layer + a linear Vmax head. Nothing about
the per-model architecture changed; what changed is training ten of them on
disjoint 1,000-image slices instead of one on a single 6,000-image slice.

**Why this is genuinely low/no-GPU, not just relabeled:** training happens
one subset and one small model at a time — the loop loads a subset, trains a
fresh `TinyCNN`, checkpoints it, and frees that subset's memory before the
next one starts (`src/cv_models/pretrain_tcir_ensemble.py`, the per-model
loop in `main()`). Peak memory/compute at any instant is bounded by one
1,000-image subset and one small CNN, never by the full 10,000-image pool or
by ten models simultaneously. This is a different resource profile from
training one larger model against the whole pool at once, which is the
concrete, defensible version of the "low/no-GPU method" claim.

**The combiner** (`CombinerNet`) is the "another model" the mentor described.
It takes the ten frozen sub-models' 32-dim embeddings, concatenated into a
320-dim vector, and learns to fuse them into one combined 32-dim embedding —
trained on its own held-out 2,000-image split, on the same Vmax-regression
task. That combined embedding is what would replace the single backbone's
embedding downstream (feature fusion, anomaly detection) if this pipeline is
adopted in production — see section 6.

## 4. Where this honestly differs from the most literal reading

The SRS's Section 5 table sketches *candidate* sub-model roles that are
task-diverse — cyclone classification, eye detection, segmentation, cloud
extent, and so on, each answering a different question. That version isn't
buildable: TCIR and insat3d only have one real per-image label between them
(Vmax), no eye-location masks, no segmentation masks, no structure
annotations. Training an "eye detector" or "segmentation" sub-model would
mean inventing labels, which this project's own rule against presenting
synthetic data as real rules out.

What's built instead is ten sub-models trained on the **same** task (Vmax
regression) but **disjoint data slices** — a bagging-style ensemble, not a
task-diverse one. This is still a real, standard, defensible multi-model
method (this is literally how ensemble/bagging methods work), and it still
satisfies the concrete instruction — split the data, train N models
independently, combine with another model, keep peak resource use low — just
worth being precise with your mentor that the "10 different specialties"
framing from the SRS's original sketch isn't what got built, because the
labels to make that real don't exist in this data.

## 5. Results

Both rows are evaluated on the exact same 2,000-image held-out test pool —
unseen by every sub-model, the combiner, and the original single backbone —
so this is a fair, controlled comparison, not two different eval sets.

| Method | Total training images | Test MAE (knots) | Test R² |
|---|---|---|---|
| Single backbone (original, 1 model) | 5,400 | **11.17** | **0.752** |
| Ensemble (10 models × 1,000 + combiner) | 9,000 (900/model) | 12.63 | 0.648 |

Per-sub-model detail (each on 900 training images, 20 epochs): validation MAE
ranged 13.3–17.4kt, R² 0.43–0.64 — noticeably weaker individually than the
single backbone's 11.5kt/0.73, as expected from 6× less data per model. The
combiner recovered a meaningful chunk of that gap on its own validation split
(11.9kt / 0.70) but not all of it on the fully-independent test set
(12.6kt / 0.65). Total wall-clock: ~25 minutes for all 10 sub-models
sequentially, CPU-only (see `train_seconds` per model in
`reports/tcir_ensemble_results.json`) — each individual job stayed small and
fast; the total time is the sum of ten small jobs, not one long one.

**Read this honestly, not as a win:** the ensemble is *not* more accurate
than the single backbone — it's about 1.5kt worse on MAE and 0.10 lower on
R², on the same held-out data. The reason is straightforward: each sub-model
only ever sees 900 training images (1,000 minus its own internal validation
split) vs. the single backbone's 5,400, and splitting the same-sized labeled
pool ten ways costs more in per-model data than the combiner recovers by
fusing them back together. What this method demonstrably buys is a **bounded
peak-resource training profile** (never more than one 1,000-image subset and
one small CNN in memory at a time) — a genuine "low/no-GPU" property — not
higher accuracy. If your mentor's ask is specifically the resource-profile
claim, this result supports it directly. If the ask is "and it should also
perform better," that isn't what this run shows, and the honest framing for
her is a real accuracy-for-resource-bound tradeoff, not a free win.

Two directions to close some of that gap, both cheap to try before drawing
final conclusions: pull more than 1,000 images into each subset (fewer, larger
subsets), or feed the combiner more than 2,000 training images. Neither was
done here to keep the run fast for a first pass.

## 6. What this does and doesn't change downstream

- **Doesn't change**: insat3d's role, `build_master_dataset.py`, the anomaly
  autoencoder, the Odisha district graph, the AI agent, the dashboard. None
  of those depend on which backbone produced the embeddings, only on the
  embeddings' shape (32-dim), which the combiner preserves.
- **Would change, only if you decide to adopt this as the production
  backbone**: `src/cv_models/extract_insat3d_features.py` currently loads
  the single-backbone checkpoint; swapping it to load the 10 sub-model
  checkpoints + combiner instead would mean re-extracting insat3d features,
  and likely retraining the anomaly autoencoder against the new embedding
  space. That's a deliberate follow-up decision, not done automatically here
  — Phase 3 was already marked "done" with working, evaluated results, and
  this document's job is to give you the comparison to decide with, not to
  force the swap.

## 7. Files produced

- `src/cv_models/pretrain_tcir_ensemble.py` — the pipeline described above
- `src/cv_models/checkpoints/ensemble/model_00.pt` … `model_09.pt` — the 10 sub-models
- `src/cv_models/checkpoints/ensemble/combiner.pt` — the combiner
- `reports/tcir_ensemble_results.json` — full numeric results (per-sub-model
  metrics, combiner metrics, final comparison)
- `reports/tcir_ensemble_comparison.png` — bar-chart comparison plot
