"""7-class arrhythmia CNN over differential signal-to-image representations (paper Fig. 4).

Channel progression 3->8->16->32->64->128 with a max-pool after each of the first four conv
blocks and a global-average-pool after the fifth, matching the figure's labelled layer sizes
(128x128x8 -> maxpool -> 64x64x16 -> maxpool -> 32x32x32 -> maxpool -> 16x16x64 -> maxpool ->
8x8x128 -> avgpool -> FC -> softmax over 7 classes).
"""
from __future__ import annotations

import torch
from torch import nn

CLASSES = ["NSR", "APB", "AFL", "AFIB", "VT", "Bigeminy", "Trigeminy"]


def _conv_block(in_ch: int, out_ch: int, pool: bool) -> nn.Sequential:
    layers = [
        nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    ]
    if pool:
        layers.append(nn.MaxPool2d(2))
    return nn.Sequential(*layers)


class ArrhythmiaCNN(nn.Module):
    def __init__(self, num_classes: int = 7):
        super().__init__()
        self.features = nn.Sequential(
            _conv_block(3, 8, pool=True),
            _conv_block(8, 16, pool=True),
            _conv_block(16, 32, pool=True),
            _conv_block(32, 64, pool=True),
            _conv_block(64, 128, pool=False),
        )
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(128, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = self.global_pool(x).flatten(1)
        return self.classifier(x)  # logits; apply softmax/cross-entropy outside
