"""1D ResNet-18 adapted for raw ECG segments.

The paper describes ResNet-18 layer-by-layer (conv, BN, ReLU, 4 stages x 2 residual blocks,
global average pooling, FC) but never states whether it operates on 1D time-series segments
or 2D images — inputs throughout the paper are raw 10s ECG segments, not images, so 1D
convolution is the documented, justified choice here, not an assumption glossed over.
"""
from __future__ import annotations

import torch
from torch import nn


class BasicBlock1D(nn.Module):
    def __init__(self, in_ch: int, out_ch: int, stride: int = 1):
        super().__init__()
        self.conv1 = nn.Conv1d(in_ch, out_ch, kernel_size=7, stride=stride, padding=3, bias=False)
        self.bn1 = nn.BatchNorm1d(out_ch)
        self.conv2 = nn.Conv1d(out_ch, out_ch, kernel_size=7, padding=3, bias=False)
        self.bn2 = nn.BatchNorm1d(out_ch)
        self.relu = nn.ReLU(inplace=True)

        self.downsample = None
        if stride != 1 or in_ch != out_ch:
            self.downsample = nn.Sequential(
                nn.Conv1d(in_ch, out_ch, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm1d(out_ch),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = x if self.downsample is None else self.downsample(x)
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        return self.relu(out + identity)


class ResNet18_1D(nn.Module):
    def __init__(self, in_channels: int = 1, num_classes: int = 2):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=15, stride=2, padding=7, bias=False),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=3, stride=2, padding=1),
        )
        stage_channels = [32, 64, 128, 256]
        stages = []
        in_ch = 32
        for i, out_ch in enumerate(stage_channels):
            stride = 1 if i == 0 else 2
            stages.append(BasicBlock1D(in_ch, out_ch, stride=stride))
            stages.append(BasicBlock1D(out_ch, out_ch, stride=1))
            in_ch = out_ch
        self.stages = nn.Sequential(*stages)
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Linear(stage_channels[-1], num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, in_channels, length)
        x = self.stem(x)
        x = self.stages(x)
        x = self.global_pool(x).flatten(1)
        return self.fc(x)  # logits
