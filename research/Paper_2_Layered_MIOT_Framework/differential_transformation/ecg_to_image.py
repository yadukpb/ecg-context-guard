"""Differential ECG signal-to-image conversion (paper's Pseudocode 1, ported to Python).

Original MATLAB:
    x = (x-min(x))/(max(x)-min(x));
    t = x(2:end)-x(1:end-1);
    y = [0 t];
    plot(x, y, 'linewidth', 2); axis off; print to image.

First image dimension = min-max normalized signal value; second = its discrete first
difference X(n)-X(n-1). Plotting (x, y) as a closed trace produces the loop-shaped 2D
patterns Fig. 5 shows per arrhythmia class. Rendered directly to a pixel array via
matplotlib's Agg backend (no temp-file round trip needed).
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def ecg_to_image(window: np.ndarray, image_size: int = 128) -> np.ndarray:
    """Return an ``(image_size, image_size, 3)`` uint8 RGB array for one ECG window."""
    x = window.astype(np.float64)
    span = x.max() - x.min()
    x_norm = (x - x.min()) / span if span > 0 else np.zeros_like(x)
    y = np.concatenate([[0.0], np.diff(x_norm)])

    dpi = 100
    fig = plt.figure(figsize=(image_size / dpi, image_size / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.plot(x_norm, y, linewidth=2, color="tab:blue")
    ax.axis("off")

    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
    plt.close(fig)
    return buf


def save_sample_images(windows_by_class: dict[str, np.ndarray], out_dir: str) -> None:
    """One representative image per class, for the report (paper's Fig. 5 equivalent)."""
    import os

    os.makedirs(out_dir, exist_ok=True)
    for class_name, window in windows_by_class.items():
        img = ecg_to_image(window)
        plt.imsave(os.path.join(out_dir, f"{class_name}.png"), img)
