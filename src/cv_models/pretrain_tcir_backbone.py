"""
Phase 3, step 1: pretrain the shared CNN backbone on TCIR (CPU-only).

Pretext task: predict cyclone max wind speed (Vmax, knots) from the IR-window
channel of a TCIR image. This is a real, labeled task (unlike insat3d, which has
no intensity ground truth), so it's used purely to teach the backbone generic
cyclone-structure convolutional filters before those filters are reused on insat3d.

Trains on a random CPU-sized subset (not the full 21k images) per the SRS's
"manageable subsets" compute strategy (section 6) -- doubly relevant with no GPU.

Usage: python src/cv_models/pretrain_tcir_backbone.py
"""

import json
import sys
import time
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backbone import TinyCNN

ROOT = Path(__file__).resolve().parents[2]
TCIR_H5 = ROOT / "data" / "raw" / "tcir_global" / "images.h5"
TCIR_LABELS = ROOT / "data" / "raw" / "tcir_global" / "labels.npy"
CHECKPOINT_DIR = ROOT / "src" / "cv_models" / "checkpoints"
REPORTS_DIR = ROOT / "reports"

N_SUBSET = 6000        # CPU-manageable subset of the 21,076 TCIR images (was 2000)
VAL_FRACTION = 0.1
EPOCHS = 20             # was 12
BATCH_SIZE = 64
LR = 1e-3
SEED = 42

# dataviz skill palette (references/palette.md): categorical slot 1 = blue, slot 2 = orange
COLOR_TRAIN = "#2a78d6"
COLOR_VAL = "#eb6834"
COLOR_SURFACE = "#fcfcfb"
COLOR_GRID = "#e1e0d9"
COLOR_INK = "#0b0b0b"
COLOR_INK_SECONDARY = "#52514e"


def main():
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)

    labels = np.load(TCIR_LABELS, allow_pickle=True)
    vmax_all = labels[:, 5].astype(np.float32)

    idx = np.sort(rng.choice(len(labels), size=N_SUBSET, replace=False))

    print(f"Loading {N_SUBSET} TCIR images (channel 0 / IR window only)...")
    t0 = time.time()
    with h5py.File(TCIR_H5, "r") as f:
        images = f["Images"]
        try:
            channel0 = images[idx, :, :, 0]  # (N, 128, 128)
        except Exception:
            # fallback if h5py rejects the mixed fancy/scalar index on this version
            channel0 = images[idx, :, :, :][:, :, :, 0]
    print(f"  loaded in {time.time() - t0:.1f}s, shape={channel0.shape}")

    vmax = vmax_all[idx]

    n_val = int(N_SUBSET * VAL_FRACTION)
    perm = rng.permutation(N_SUBSET)
    val_idx, train_idx = perm[:n_val], perm[n_val:]

    x_mean, x_std = channel0[train_idx].mean(), channel0[train_idx].std() + 1e-6
    y_mean, y_std = vmax[train_idx].mean(), vmax[train_idx].std() + 1e-6

    def to_tensor(imgs, targets):
        x = (imgs.astype(np.float32) - x_mean) / x_std
        x = torch.from_numpy(x).unsqueeze(1)  # (N,1,128,128)
        y = torch.from_numpy(((targets - y_mean) / y_std).astype(np.float32)).unsqueeze(1)
        return x, y

    x_train, y_train = to_tensor(channel0[train_idx], vmax[train_idx])
    x_val, y_val = to_tensor(channel0[val_idx], vmax[val_idx])

    model = TinyCNN(embed_dim=32)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()

    n_train = x_train.shape[0]
    print(f"\nTraining TinyCNN backbone: {n_train} train / {n_val} val, {EPOCHS} epochs, CPU only")
    history = {"epoch": [], "train_mse": [], "val_mse": [], "val_mae_kt": [], "val_r2": []}
    t0 = time.time()
    for epoch in range(1, EPOCHS + 1):
        model.train()
        perm_e = torch.randperm(n_train)
        epoch_loss = 0.0
        for start in range(0, n_train, BATCH_SIZE):
            batch_idx = perm_e[start:start + BATCH_SIZE]
            xb, yb = x_train[batch_idx], y_train[batch_idx]
            opt.zero_grad()
            pred, _ = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            opt.step()
            epoch_loss += loss.item() * xb.size(0)
        epoch_loss /= n_train

        model.eval()
        with torch.no_grad():
            val_pred, _ = model(x_val)
            val_loss = loss_fn(val_pred, y_val).item()
            val_pred_kt = val_pred.numpy().ravel() * y_std + y_mean
            val_true_kt = y_val.numpy().ravel() * y_std + y_mean
            ss_res = np.sum((val_true_kt - val_pred_kt) ** 2)
            ss_tot = np.sum((val_true_kt - val_true_kt.mean()) ** 2)
            r2 = 1 - ss_res / ss_tot
            mae_kt = np.mean(np.abs(val_true_kt - val_pred_kt))

        print(f"  epoch {epoch:2d}/{EPOCHS}  train_mse={epoch_loss:.4f}  "
              f"val_mse={val_loss:.4f}  val_MAE={mae_kt:.1f}kt  val_R2={r2:.3f}")

        history["epoch"].append(epoch)
        history["train_mse"].append(epoch_loss)
        history["val_mse"].append(val_loss)
        history["val_mae_kt"].append(mae_kt)
        history["val_r2"].append(r2)

    print(f"\nTraining done in {time.time() - t0:.1f}s")

    # dead-dimension check (this is what LeakyReLU is meant to fix vs. the first run)
    model.eval()
    with torch.no_grad():
        _, train_embeds = model(x_train)
    dead_dims = int((train_embeds.std(dim=0) < 0.01).sum().item())
    print(f"Dead embedding dimensions (std < 0.01 on train set): {dead_dims}/{model.embed_dim}")

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    ckpt_path = CHECKPOINT_DIR / "tcir_backbone.pt"
    torch.save({
        "state_dict": model.state_dict(),
        "embed_dim": model.embed_dim,
        "x_mean": float(x_mean),
        "x_std": float(x_std),
        "y_mean": float(y_mean),
        "y_std": float(y_std),
        "n_train_images": int(n_train),
        "pretext_task": "TCIR channel-0 (IR window) -> Vmax (knots) regression",
        "final_val_mae_kt": float(mae_kt),
        "final_val_r2": float(r2),
        "dead_dims": dead_dims,
    }, ckpt_path)
    print(f"Saved checkpoint: {ckpt_path}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORTS_DIR / "tcir_backbone_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, default=float)  # numpy float32 isn't natively JSON-serializable

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), facecolor=COLOR_SURFACE)
    for ax in axes:
        ax.set_facecolor(COLOR_SURFACE)
        ax.grid(True, color=COLOR_GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color(COLOR_GRID)
        ax.tick_params(colors=COLOR_INK_SECONDARY, labelsize=9)
        ax.set_xlabel("Epoch", color=COLOR_INK_SECONDARY, fontsize=10)

    axes[0].plot(history["epoch"], history["train_mse"], color=COLOR_TRAIN, linewidth=2, label="Train MSE")
    axes[0].plot(history["epoch"], history["val_mse"], color=COLOR_VAL, linewidth=2, label="Val MSE")
    axes[0].set_ylabel("MSE (standardized Vmax)", color=COLOR_INK_SECONDARY, fontsize=10)
    axes[0].set_title("Training loss", color=COLOR_INK, fontsize=11, loc="left")
    axes[0].legend(frameon=False, fontsize=9, labelcolor=COLOR_INK_SECONDARY)

    axes[1].plot(history["epoch"], history["val_mae_kt"], color=COLOR_VAL, linewidth=2)
    axes[1].set_ylabel("Val MAE (knots)", color=COLOR_INK_SECONDARY, fontsize=10)
    axes[1].set_title("Validation error", color=COLOR_INK, fontsize=11, loc="left")

    axes[2].plot(history["epoch"], history["val_r2"], color=COLOR_TRAIN, linewidth=2)
    axes[2].set_ylabel("Val R²", color=COLOR_INK_SECONDARY, fontsize=10)
    axes[2].set_title("Validation fit", color=COLOR_INK, fontsize=11, loc="left")

    fig.suptitle(f"TCIR backbone pretraining -- {n_train} images, {EPOCHS} epochs", color=COLOR_INK, fontsize=12)
    fig.tight_layout()
    plot_path = REPORTS_DIR / "tcir_backbone_training_curves.png"
    fig.savefig(plot_path, dpi=150, facecolor=COLOR_SURFACE)
    plt.close(fig)
    print(f"Saved training curves: {plot_path}")


if __name__ == "__main__":
    main()
