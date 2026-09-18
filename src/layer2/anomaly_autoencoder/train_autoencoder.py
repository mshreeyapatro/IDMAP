"""
Phase 6: anomaly detection via Autoencoder (SRS section 10).

Unsupervised by design -- needs no risk/intensity labels, unlike XGBoost (Phase 5),
which is currently blocked (see chat: no label exists anywhere in the insat3d data).

CAVEAT vs. the SRS's original framing: section 10 describes the autoencoder learning
"normal" patterns across a cyclone's *temporal evolution* (a sequence of states over
time) and flagging unusual evolution. We don't have per-image timestamps, so a
temporal-sequence autoencoder isn't possible yet. What's built here instead is a
*cross-sectional* autoencoder: it learns what a "typical" cyclone visual-feature
embedding looks like across all 276 images, and flags individual images/events whose
embedding reconstructs poorly as visual outliers. Re-architect to a sequence model
(e.g. LSTM-autoencoder) once real timestamps make per-storm sequences possible.

Usage: python src/layer2/anomaly_autoencoder/train_autoencoder.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[3]
CV_FEATURES_CSV = ROOT / "data" / "processed" / "insat3d_cv_features.csv"
CHECKPOINT_DIR = ROOT / "src" / "layer2" / "anomaly_autoencoder" / "checkpoints"
OUT_CSV = ROOT / "data" / "processed" / "insat3d_anomaly_scores.csv"
REPORTS_DIR = ROOT / "reports"

BOTTLENECK = 8
EPOCHS = 200
LR = 1e-3
SEED = 42
ANOMALY_PERCENTILE = 95  # data-driven threshold: top 5% of TRAIN reconstruction error

# dataviz skill palette (references/palette.md)
COLOR_SURFACE = "#fcfcfb"
COLOR_GRID = "#e1e0d9"
COLOR_INK = "#0b0b0b"
COLOR_INK_SECONDARY = "#52514e"
# categorical slots 1-3 (validated all-pairs for exactly this many categories)
SPLIT_COLORS = {"train": "#2a78d6", "val": "#eb6834", "test": "#1baf7a"}
# status palette: critical for flagged, muted chart-chrome gray for normal
COLOR_ANOMALY = "#d03b3b"
COLOR_NORMAL = "#898781"


class AE(nn.Module):
    def __init__(self, in_dim=32, bottleneck=BOTTLENECK):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, 16), nn.ReLU(),
            nn.Linear(16, bottleneck), nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(bottleneck, 16), nn.ReLU(),
            nn.Linear(16, in_dim),
        )

    def forward(self, x):
        z = self.encoder(x)
        return self.decoder(z), z


def main():
    torch.manual_seed(SEED)
    df = pd.read_csv(CV_FEATURES_CSV)
    embed_cols = sorted(c for c in df.columns if c.startswith("embed_"))

    x_all_full = df[embed_cols].values.astype(np.float32)
    train_mask = (df["split"] == "train").values

    # drop "dead" embedding dimensions (always ~0 in train -- a dying-ReLU artifact
    # of a lightly-trained TCIR backbone): their near-zero std would blow up
    # under normalization for any non-train sample that happens to be nonzero there,
    # producing spurious multi-order-of-magnitude "anomalies" that are a normalization
    # bug, not a real signal. (Should be rare/absent after the LeakyReLU fix -- this
    # check stays as a safety net regardless.)
    raw_std = x_all_full[train_mask].std(axis=0)
    active = raw_std > 0.01
    active_cols = [c for c, keep in zip(embed_cols, active) if keep]
    print(f"Using {len(active_cols)}/{len(embed_cols)} active embedding dims "
          f"(dropped {len(embed_cols) - len(active_cols)} dead dims: "
          f"{[c for c, keep in zip(embed_cols, active) if not keep]})")

    x_all = x_all_full[:, active]
    mean = x_all[train_mask].mean(axis=0)
    std = x_all[train_mask].std(axis=0) + 1e-6
    x_norm = (x_all - mean) / std

    x_train = torch.from_numpy(x_norm[train_mask])
    x_full = torch.from_numpy(x_norm)

    model = AE(in_dim=len(active_cols))
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()

    print(f"Training autoencoder: {x_train.shape[0]} train images, "
          f"32 -> {BOTTLENECK} -> 32, {EPOCHS} epochs, CPU only")
    for epoch in range(1, EPOCHS + 1):
        model.train()
        opt.zero_grad()
        recon, _ = model(x_train)
        loss = loss_fn(recon, x_train)
        loss.backward()
        opt.step()
        if epoch % 40 == 0 or epoch == 1:
            print(f"  epoch {epoch:3d}/{EPOCHS}  train_recon_mse={loss.item():.4f}")

    model.eval()
    with torch.no_grad():
        recon_train, _ = model(x_train)
        per_image_train_err = ((recon_train - x_train) ** 2).mean(dim=1).numpy()

        recon_full, _ = model(x_full)
        per_image_err = ((recon_full - x_full) ** 2).mean(dim=1).numpy()

    threshold = float(np.percentile(per_image_train_err, ANOMALY_PERCENTILE))

    df["reconstruction_error"] = per_image_err
    df["is_anomaly"] = df["reconstruction_error"] > threshold
    out = df[["base_id", "split", "modality", "filename",
              "reconstruction_error", "is_anomaly"]].sort_values(
        "reconstruction_error", ascending=False)
    out.to_csv(OUT_CSV, index=False)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(),
        "bottleneck": BOTTLENECK,
        "active_embed_cols": active_cols,
        "embed_mean": mean.tolist(),
        "embed_std": std.tolist(),
        "anomaly_threshold": threshold,
        "anomaly_percentile": ANOMALY_PERCENTILE,
    }, CHECKPOINT_DIR / "autoencoder.pt")

    n_anom = int(df["is_anomaly"].sum())
    print(f"\nDone. Threshold (train {ANOMALY_PERCENTILE}th pct): {threshold:.4f}")
    print(f"Flagged {n_anom}/{len(df)} images as anomalous across all splits.")
    print(f"Top 5 most anomalous images:")
    print(out.head(5).to_string(index=False))
    print(f"\nSaved: {OUT_CSV}")

    # --- embedding space visualization: PCA to 2D, two views on the same layout ---
    pca = PCA(n_components=2, random_state=SEED)
    coords = pca.fit_transform(x_norm)
    var_explained = pca.explained_variance_ratio_

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), facecolor=COLOR_SURFACE)
    for ax in axes:
        ax.set_facecolor(COLOR_SURFACE)
        ax.grid(True, color=COLOR_GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color(COLOR_GRID)
        ax.tick_params(colors=COLOR_INK_SECONDARY, labelsize=9)
        ax.set_xlabel(f"PC1 ({var_explained[0]*100:.0f}% var)", color=COLOR_INK_SECONDARY, fontsize=10)
        ax.set_ylabel(f"PC2 ({var_explained[1]*100:.0f}% var)", color=COLOR_INK_SECONDARY, fontsize=10)

    split_markers = {"train": "o", "val": "s", "test": "D"}
    for split, color in SPLIT_COLORS.items():
        mask = (df["split"] == split).values
        axes[0].scatter(coords[mask, 0], coords[mask, 1], s=28, color=color,
                         marker=split_markers[split], label=split,
                         edgecolors=COLOR_SURFACE, linewidths=0.5, alpha=0.9)
    axes[0].set_title("By split", color=COLOR_INK, fontsize=11, loc="left")
    axes[0].legend(frameon=False, fontsize=9, labelcolor=COLOR_INK_SECONDARY)

    normal_mask = ~df["is_anomaly"].values
    axes[1].scatter(coords[normal_mask, 0], coords[normal_mask, 1], s=24, color=COLOR_NORMAL,
                     label="normal", edgecolors=COLOR_SURFACE, linewidths=0.5, alpha=0.8)
    axes[1].scatter(coords[~normal_mask, 0], coords[~normal_mask, 1], s=48, color=COLOR_ANOMALY,
                     label="flagged anomalous", edgecolors=COLOR_SURFACE, linewidths=0.6, marker="^")
    axes[1].set_title("By anomaly flag", color=COLOR_INK, fontsize=11, loc="left")
    axes[1].legend(frameon=False, fontsize=9, labelcolor=COLOR_INK_SECONDARY)

    fig.suptitle(f"Insat3d CV embedding space (PCA, {len(active_cols)} active dims -> 2D)",
                 color=COLOR_INK, fontsize=12)
    fig.tight_layout()
    plot_path = REPORTS_DIR / "embedding_space.png"
    fig.savefig(plot_path, dpi=150, facecolor=COLOR_SURFACE)
    plt.close(fig)
    print(f"Saved embedding visualization: {plot_path}")


if __name__ == "__main__":
    main()
