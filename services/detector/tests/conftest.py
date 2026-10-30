"""Shared fixtures. Downloads one real MIT-BIH record on first run (needs internet once);
cached under data/mitdb afterwards, same cache the live service uses.
"""
import numpy as np
import pytest

from app import mitdb
from app.config import FS_HZ, WINDOW_SEC

WINDOW_SAMPLES = WINDOW_SEC * FS_HZ


@pytest.fixture(scope="session")
def record_100_signal() -> np.ndarray:
    return mitdb.lead_ii_signal("100")


@pytest.fixture
def genuine_window(record_100_signal):
    """One clean 2s window, pulled well past the start to avoid any lead-in artifacts."""
    start = WINDOW_SAMPLES * 20
    return record_100_signal[start : start + WINDOW_SAMPLES]


@pytest.fixture
def calibration_windows(record_100_signal):
    """A run of consecutive windows suitable for building a baseline."""
    from app.signal_proc import preprocess

    windows = []
    for i in range(30):
        start = WINDOW_SAMPLES * i
        raw = record_100_signal[start : start + WINDOW_SAMPLES]
        windows.append(preprocess(raw, FS_HZ))
    return windows
