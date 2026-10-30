import numpy as np

from app.config import FS_HZ
from app.signal_proc import extract_features, preprocess


def test_preprocess_and_features_are_deterministic(genuine_window):
    processed_a = preprocess(genuine_window, FS_HZ)
    processed_b = preprocess(genuine_window, FS_HZ)
    assert np.allclose(processed_a, processed_b)

    features_a = extract_features(processed_a, FS_HZ)
    features_b = extract_features(processed_b, FS_HZ)
    assert features_a.to_dict() == features_b.to_dict()


def test_extracted_heart_rate_is_physiologically_plausible(genuine_window):
    processed = preprocess(genuine_window, FS_HZ)
    features = extract_features(processed, FS_HZ)

    assert features.n_beats >= 1
    # A real MIT-BIH segment should read as a plausible human heart rate, not noise.
    assert 30.0 <= features.heart_rate_bpm <= 220.0
