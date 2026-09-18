"""Shared tiny CNN backbone used for TCIR pretraining and insat3d feature extraction.

Single-channel, 128x128 input by design: TCIR's 4 channels are physical sensor
channels (IR window / water vapor / passive-microwave / IR2) with no equivalent
in insat3d's rendered RGB JPEGs, so channel-for-channel transfer would be scientifically
invalid. Instead both domains are reduced to a single grayscale "cloud structure" channel
and the backbone transfers generic texture/shape filters, not physical channel semantics.

Uses LeakyReLU (not ReLU): the first training run showed 17/32 embedding
dimensions permanently dead (always exactly 0) on the training distribution --
classic dying-ReLU on a small/lightly-trained net. LeakyReLU keeps a small
gradient for negative activations so units can recover instead of dying.
"""

import torch
import torch.nn as nn


class TinyCNN(nn.Module):
    def __init__(self, embed_dim: int = 32):
        super().__init__()
        self.embed_dim = embed_dim
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.LeakyReLU(0.1), nn.MaxPool2d(2),   # 128 -> 64
            nn.Conv2d(16, 32, 3, padding=1), nn.LeakyReLU(0.1), nn.MaxPool2d(2),  # 64 -> 32
            nn.Conv2d(32, 64, 3, padding=1), nn.LeakyReLU(0.1), nn.MaxPool2d(2),  # 32 -> 16
            nn.AdaptiveAvgPool2d(4),                                      # -> 4x4
        )
        self.embed = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 4 * 4, embed_dim),
            nn.LeakyReLU(0.1),
        )
        self.head = nn.Linear(embed_dim, 1)

    def forward(self, x: torch.Tensor):
        f = self.features(x)
        e = self.embed(f)
        out = self.head(e)
        return out, e
