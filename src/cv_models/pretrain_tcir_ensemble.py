"""
Phase 3 (mentor-directed variant): multi-model TCIR pretraining with a learned
combiner, instead of one backbone trained on one subset.

This is the SRS's own Section 5/6 architecture ("Multi-Model Satellite Vision
Architecture" / "GPU-/Compute Strategy"), actually built rather than only
planned: TCIR's images are split into ~1,000-image subsets, N lightweight CNNs
are trained independently and SEQUENTIALLY (one model's data/weights are loaded,
trained, checkpointed, and released before the next model starts -- so peak
memory/compute is bounded by ONE subset + ONE small model at a time, never by
the full dataset or by N models at once), and their frozen embeddings are then
fused by a small learned combiner network into a single embedding -- this is
what "low/no-GPU" means here: it's a genuinely different resource profile than
training one larger model on the full pool at once, not just a rebranding.

Scope note for accuracy: TCIR only has one real label (Vmax), so every
sub-model is trained on the SAME pretext task (Vmax regression) on a disjoint
1,000-image slice -- this is a bagging-style ensemble-of-data-subsets, not the
task-diverse ensemble (eye detector, segmentation, etc.) the SRS's Section 5
table sketches as *candidates*, since insat3d/TCIR have no per-task labels
(masks, eye-location, etc.) to train those other tasks against. See
docs/multi_model_ensemble_method.md for the full writeup and results.

insat3d is NOT split this way -- it only has ~140 raw images across 66 events,
nowhere near enough for 1,000-image subsets. It keeps its existing role:
feature extraction input for the (now ensembled) backbone, unchanged.

Usage: python src/cv_models/pretrain_tcir_ensemble.py
"""

import gc
import json
import time
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backbone import TinyCNN

ROOT = Path(__file__).resolve().parents[2]
TCIR_H5 = ROOT / "data" / "raw" / "tcir_global" / "images.h5"
TCIR_LABELS = ROOT / "data" / "raw" / "tcir_global" / "labels.npy"
SINGLE_BACKBONE_CKPT = ROOT / "src" / "cv_models" / "checkpoints" / "tcir_backbone.pt"
ENSEMBLE_DIR = ROOT / "src" / "cv_models" / "checkpoints" / "ensemble"
REPORTS_DIR = ROOT / "reports"

N_MODELS = 10          # matches the mentor's "~10,000 images, ~1,000 each"
IMAGES_PER_MODEL = 1000
COMBINER_HOLDOUT = 2000   # disjoint from the N_MODELS training pool -- trains the combiner
TEST_HOLDOUT = 2000       # disjoint from both -- final apples-to-apples evaluation only
EPOCHS_PER_MODEL = 20
COMBINER_EPOCHS = 30
BATCH_SIZE = 64
LR = 1e-3
EMBED_DIM = 32
SEED = 42

COLOR_A = "#2a78d6"   # single backbone
COLOR_B = "#eb6834"   # ensemble + combiner
COLOR_SURFACE = "#fcfcfb"
COLOR_GRID = "#e1e0d9"
COLOR_INK = "#0b0b0b"
COLOR_INK_SECONDARY = "#52514e"


class CombinerNet(nn.Module):
    """Fuses N frozen sub-model embeddings (concatenated) into one combined
    embedding + a Vmax prediction -- itself a small trained model, per the
    mentor's "combine using another model" instruction."""

    def __init__(self, in_dim: int, embed_dim: int = EMBED_DIM):
        super().__init__()
        self.embed_dim = embed_dim
        self.reduce = nn.Sequential(
            nn.Linear(in_dim, 64), nn.LeakyReLU(0.1),
            nn.Linear(64, embed_dim), nn.LeakyReLU(0.1),
        )
        self.head = nn.Linear(embed_dim, 1)

    def forward(self, x):
        e = self.reduce(x)
        return self.head(e), e


def load_channel0(indices: np.ndarray) -> np.ndarray:
    """h5py fancy indexing requires strictly increasing indices -- sort, load,
    then restore the caller's original order."""
    order = np.argsort(indices)
    sorted_idx = indices[order]
    with h5py.File(TCIR_H5, "r") as f:
        imgs = f["Images"][sorted_idx, :, :, 0]
    inverse = np.argsort(order)
    return imgs[inverse]


def train_one_model(images: np.ndarray, vmax: np.ndarray, model_idx: int) -> dict:
    """One fully independent training job: load subset (already loaded by
    caller) -> fresh model+weights -> train -> validate -> checkpoint. Locals
    are dropped at the end of this call so the next job starts clean."""
    rng = np.random.default_rng(SEED + model_idx)
    n = len(images)
    n_val = max(1, int(n * 0.1))
    perm = rng.permutation(n)
    val_idx, train_idx = perm[:n_val], perm[n_val:]

    x_mean, x_std = images[train_idx].mean(), images[train_idx].std() + 1e-6
    y_mean, y_std = vmax[train_idx].mean(), vmax[train_idx].std() + 1e-6

    def to_tensor(imgs, targets):
        x = torch.from_numpy(((imgs.astype(np.float32) - x_mean) / x_std)).unsqueeze(1)
        y = torch.from_numpy(((targets - y_mean) / y_std).astype(np.float32)).unsqueeze(1)
        return x, y

    x_train, y_train = to_tensor(images[train_idx], vmax[train_idx])
    x_val, y_val = to_tensor(images[val_idx], vmax[val_idx])

    model = TinyCNN(embed_dim=EMBED_DIM)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()
    n_train = x_train.shape[0]

    for epoch in range(1, EPOCHS_PER_MODEL + 1):
        model.train()
        perm_e = torch.randperm(n_train)
        for start in range(0, n_train, BATCH_SIZE):
            batch_idx = perm_e[start:start + BATCH_SIZE]
            xb, yb = x_train[batch_idx], y_train[batch_idx]
            opt.zero_grad()
            pred, _ = model(xb)
            loss_fn(pred, yb).backward()
            opt.step()

    model.eval()
    with torch.no_grad():
        val_pred, _ = model(x_val)
        val_pred_kt = val_pred.numpy().ravel() * y_std + y_mean
        val_true_kt = y_val.numpy().ravel() * y_std + y_mean
    mae_kt = float(np.mean(np.abs(val_true_kt - val_pred_kt)))
    ss_res = np.sum((val_true_kt - val_pred_kt) ** 2)
    ss_tot = np.sum((val_true_kt - val_true_kt.mean()) ** 2)
    r2 = float(1 - ss_res / ss_tot)

    ENSEMBLE_DIR.mkdir(parents=True, exist_ok=True)
    ckpt_path = ENSEMBLE_DIR / f"model_{model_idx:02d}.pt"
    torch.save({
        "state_dict": model.state_dict(),
        "embed_dim": EMBED_DIM,
        "x_mean": float(x_mean), "x_std": float(x_std),
        "y_mean": float(y_mean), "y_std": float(y_std),
        "n_train_images": int(n_train),
        "val_mae_kt": mae_kt, "val_r2": r2,
    }, ckpt_path)

    return {"model_idx": model_idx, "n_train": n_train, "val_mae_kt": mae_kt, "val_r2": r2, "ckpt": str(ckpt_path)}


def embed_with_frozen_model(ckpt: dict, images: np.ndarray) -> np.ndarray:
    model = TinyCNN(embed_dim=ckpt["embed_dim"])
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    x = torch.from_numpy(((images.astype(np.float32) - ckpt["x_mean"]) / ckpt["x_std"])).unsqueeze(1)
    with torch.no_grad():
        _, e = model(x)
    return e.numpy()


def predict_with_frozen_model(ckpt: dict, images: np.ndarray) -> np.ndarray:
    model = TinyCNN(embed_dim=ckpt["embed_dim"])
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    x = torch.from_numpy(((images.astype(np.float32) - ckpt["x_mean"]) / ckpt["x_std"])).unsqueeze(1)
    with torch.no_grad():
        pred, _ = model(x)
    return pred.numpy().ravel() * ckpt["y_std"] + ckpt["y_mean"]


def main():
    print("=" * 70)
    print("PHASE 3 (multi-model variant): sequential TCIR sub-model training")
    print("=" * 70)
    rng = np.random.default_rng(SEED)
    labels = np.load(TCIR_LABELS, allow_pickle=True)
    vmax_all = labels[:, 5].astype(np.float32)

    shuffled = rng.permutation(len(labels))
    subset_pool = shuffled[: N_MODELS * IMAGES_PER_MODEL]
    combiner_idx = np.sort(shuffled[N_MODELS * IMAGES_PER_MODEL: N_MODELS * IMAGES_PER_MODEL + COMBINER_HOLDOUT])
    test_idx = np.sort(shuffled[
        N_MODELS * IMAGES_PER_MODEL + COMBINER_HOLDOUT:
        N_MODELS * IMAGES_PER_MODEL + COMBINER_HOLDOUT + TEST_HOLDOUT
    ])
    print(f"TCIR pool: {len(labels)} images total. Using {N_MODELS}x{IMAGES_PER_MODEL} = "
          f"{N_MODELS * IMAGES_PER_MODEL} for sub-models, {COMBINER_HOLDOUT} for the combiner, "
          f"{TEST_HOLDOUT} held out for final evaluation (all three pools disjoint).")

    sub_model_results = []
    t_all = time.time()
    for i in range(N_MODELS):
        idx_i = np.sort(subset_pool[i * IMAGES_PER_MODEL:(i + 1) * IMAGES_PER_MODEL])
        t0 = time.time()
        images = load_channel0(idx_i)
        vmax = vmax_all[idx_i]
        result = train_one_model(images, vmax, i)
        result["train_seconds"] = round(time.time() - t0, 1)
        sub_model_results.append(result)
        print(f"  [model {i+1}/{N_MODELS}] {result['n_train']} train imgs, "
              f"val MAE={result['val_mae_kt']:.1f}kt, val R2={result['val_r2']:.3f}, "
              f"{result['train_seconds']}s")
        del images, vmax
        gc.collect()

    print(f"\nAll {N_MODELS} sub-models trained in {time.time() - t_all:.1f}s total")

    # ---- Combiner: fuse frozen sub-model embeddings into one embedding ----
    print("\nTraining combiner on frozen sub-model embeddings...")
    sub_ckpts = [torch.load(ENSEMBLE_DIR / f"model_{i:02d}.pt", weights_only=False) for i in range(N_MODELS)]

    combiner_images = load_channel0(combiner_idx)
    combiner_vmax = vmax_all[combiner_idx]
    stacked = np.concatenate([embed_with_frozen_model(c, combiner_images) for c in sub_ckpts], axis=1)  # (N, N_MODELS*EMBED_DIM)

    rng_c = np.random.default_rng(SEED + 1000)
    n_c = len(combiner_idx)
    n_val_c = int(n_c * 0.1)
    perm_c = rng_c.permutation(n_c)
    val_c, train_c = perm_c[:n_val_c], perm_c[n_val_c:]

    cx_mean, cx_std = stacked[train_c].mean(0, keepdims=True), stacked[train_c].std(0, keepdims=True) + 1e-6
    cy_mean, cy_std = combiner_vmax[train_c].mean(), combiner_vmax[train_c].std() + 1e-6

    x_train_c = torch.from_numpy(((stacked[train_c] - cx_mean) / cx_std).astype(np.float32))
    y_train_c = torch.from_numpy(((combiner_vmax[train_c] - cy_mean) / cy_std).astype(np.float32)).unsqueeze(1)
    x_val_c = torch.from_numpy(((stacked[val_c] - cx_mean) / cx_std).astype(np.float32))
    y_val_c = torch.from_numpy(((combiner_vmax[val_c] - cy_mean) / cy_std).astype(np.float32)).unsqueeze(1)

    combiner = CombinerNet(in_dim=stacked.shape[1], embed_dim=EMBED_DIM)
    opt = torch.optim.Adam(combiner.parameters(), lr=LR)
    loss_fn = nn.MSELoss()
    n_train_c = x_train_c.shape[0]
    combiner_history = {"epoch": [], "train_mse": [], "val_mae_kt": [], "val_r2": []}
    for epoch in range(1, COMBINER_EPOCHS + 1):
        combiner.train()
        perm_e = torch.randperm(n_train_c)
        epoch_loss = 0.0
        for start in range(0, n_train_c, BATCH_SIZE):
            b = perm_e[start:start + BATCH_SIZE]
            opt.zero_grad()
            pred, _ = combiner(x_train_c[b])
            loss = loss_fn(pred, y_train_c[b])
            loss.backward()
            opt.step()
            epoch_loss += loss.item() * len(b)
        epoch_loss /= n_train_c

        combiner.eval()
        with torch.no_grad():
            val_pred, _ = combiner(x_val_c)
            val_pred_kt = val_pred.numpy().ravel() * cy_std + cy_mean
            val_true_kt = y_val_c.numpy().ravel() * cy_std + cy_mean
        mae = float(np.mean(np.abs(val_true_kt - val_pred_kt)))
        ss_res = np.sum((val_true_kt - val_pred_kt) ** 2)
        ss_tot = np.sum((val_true_kt - val_true_kt.mean()) ** 2)
        r2 = float(1 - ss_res / ss_tot)
        combiner_history["epoch"].append(epoch)
        combiner_history["train_mse"].append(epoch_loss)
        combiner_history["val_mae_kt"].append(mae)
        combiner_history["val_r2"].append(r2)

    print(f"  combiner val MAE={combiner_history['val_mae_kt'][-1]:.1f}kt, "
          f"val R2={combiner_history['val_r2'][-1]:.3f} (on its own held-out split)")

    torch.save({
        "state_dict": combiner.state_dict(),
        "in_dim": stacked.shape[1],
        "embed_dim": EMBED_DIM,
        "n_sub_models": N_MODELS,
        "cx_mean": cx_mean, "cx_std": cx_std,
        "cy_mean": float(cy_mean), "cy_std": float(cy_std),
    }, ENSEMBLE_DIR / "combiner.pt")

    # ---- Final apples-to-apples evaluation on a fully unseen test pool ----
    print("\nEvaluating on the held-out test pool (unseen by every sub-model AND the combiner)...")
    test_images = load_channel0(test_idx)
    test_vmax = vmax_all[test_idx]

    test_stacked = np.concatenate([embed_with_frozen_model(c, test_images) for c in sub_ckpts], axis=1)
    x_test = torch.from_numpy(((test_stacked - cx_mean) / cx_std).astype(np.float32))
    combiner.eval()
    with torch.no_grad():
        ens_pred, _ = combiner(x_test)
    ens_pred_kt = ens_pred.numpy().ravel() * cy_std + cy_mean
    ens_mae = float(np.mean(np.abs(test_vmax - ens_pred_kt)))
    ss_res = np.sum((test_vmax - ens_pred_kt) ** 2)
    ss_tot = np.sum((test_vmax - test_vmax.mean()) ** 2)
    ens_r2 = float(1 - ss_res / ss_tot)

    single_mae, single_r2 = None, None
    if SINGLE_BACKBONE_CKPT.exists():
        single_ckpt = torch.load(SINGLE_BACKBONE_CKPT, weights_only=False)
        single_pred_kt = predict_with_frozen_model(single_ckpt, test_images)
        single_mae = float(np.mean(np.abs(test_vmax - single_pred_kt)))
        ss_res_s = np.sum((test_vmax - single_pred_kt) ** 2)
        single_r2 = float(1 - ss_res_s / ss_tot)

    print(f"\n{'Method':<30} {'Test MAE (kt)':>15} {'Test R2':>10}")
    print(f"{'-'*30} {'-'*15} {'-'*10}")
    if single_mae is not None:
        print(f"{'Single backbone (baseline)':<30} {single_mae:>15.2f} {single_r2:>10.3f}")
    print(f"{f'Ensemble ({N_MODELS} models + combiner)':<30} {ens_mae:>15.2f} {ens_r2:>10.3f}")

    results = {
        "n_models": N_MODELS, "images_per_model": IMAGES_PER_MODEL,
        "combiner_holdout": COMBINER_HOLDOUT, "test_holdout": TEST_HOLDOUT,
        "sub_model_results": sub_model_results,
        "combiner_val_mae_kt": combiner_history["val_mae_kt"][-1],
        "combiner_val_r2": combiner_history["val_r2"][-1],
        "test_ensemble_mae_kt": ens_mae, "test_ensemble_r2": ens_r2,
        "test_single_backbone_mae_kt": single_mae, "test_single_backbone_r2": single_r2,
        "total_train_seconds": round(time.time() - t_all, 1),
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORTS_DIR / "tcir_ensemble_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=float)
    print(f"\nSaved: {REPORTS_DIR / 'tcir_ensemble_results.json'}")

    # ---- Comparison plot ----
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), facecolor=COLOR_SURFACE)
    for ax in axes:
        ax.set_facecolor(COLOR_SURFACE)
        ax.grid(True, axis="y", color=COLOR_GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color(COLOR_GRID)
        ax.tick_params(colors=COLOR_INK_SECONDARY, labelsize=9)

    labels_x = ["Single backbone", "Ensemble + combiner"]
    maes = [single_mae or 0, ens_mae]
    r2s = [single_r2 or 0, ens_r2]
    colors = [COLOR_A, COLOR_B]
    axes[0].bar(labels_x, maes, color=colors)
    axes[0].set_ylabel("Test MAE (knots)", color=COLOR_INK_SECONDARY, fontsize=10)
    axes[0].set_title("Lower is better", color=COLOR_INK, fontsize=11, loc="left")
    axes[1].bar(labels_x, r2s, color=colors)
    axes[1].set_ylabel("Test R²", color=COLOR_INK_SECONDARY, fontsize=10)
    axes[1].set_title("Higher is better", color=COLOR_INK, fontsize=11, loc="left")
    fig.suptitle("Single backbone vs. 10-model ensemble+combiner (same held-out test set)",
                 color=COLOR_INK, fontsize=12)
    fig.tight_layout()
    plot_path = REPORTS_DIR / "tcir_ensemble_comparison.png"
    fig.savefig(plot_path, dpi=150, facecolor=COLOR_SURFACE)
    plt.close(fig)
    print(f"Saved: {plot_path}")


if __name__ == "__main__":
    main()
