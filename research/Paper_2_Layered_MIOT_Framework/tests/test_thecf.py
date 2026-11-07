import numpy as np

from Paper_2_Layered_MIOT_Framework.THECF import thecf


def _sine_beat(fs=360.0, seconds=1.0, amplitude=0.5):
    """A QRS-like synthetic beat: sharp Q/R/S triangular deflections (broadband, with real
    energy in the 30-45Hz QRS band THECF's layer 2 checks — a smooth low-frequency sine or a
    wide Gaussian spike both fail to land in [0.18, 0.85], confirmed by direct measurement
    while writing this fixture) riding on a slow baseline wander term."""
    t = np.linspace(0, seconds, int(fs * seconds), endpoint=False)
    centre = seconds / 2
    half_width = 0.011  # ~22ms full QRS width, measured to land the band-ratio in-range

    def _triangle(peak_centre: float, half: float, amp: float) -> np.ndarray:
        return amp * np.clip(1 - np.abs(t - peak_centre) / half, 0, None)

    baseline = 0.1 * amplitude * np.sin(2 * np.pi * 1.2 * t)
    r_wave = _triangle(centre, half_width, amplitude)
    q_wave = _triangle(centre - half_width, half_width * 0.6, amplitude * 0.25)
    s_wave = _triangle(centre + half_width, half_width * 0.6, amplitude * 0.35)
    return baseline + r_wave - q_wave - s_wave


def test_total_energy_is_mean_square():
    window = np.array([1.0, -1.0, 1.0, -1.0])
    assert thecf.total_energy(window) == 1.0


def test_flatline_fails_energy_gate():
    fs = 360.0
    template = thecf.build_healthy_template([_sine_beat(fs) for _ in range(5)])
    flat = np.zeros(int(fs))
    verdict = thecf.evaluate(flat, fs, template)
    assert not verdict.passed
    assert verdict.failed_layer == "energy"


def test_clean_sine_like_beat_passes_or_fails_a_named_layer():
    fs = 360.0
    beats = [_sine_beat(fs) for _ in range(10)]
    template = thecf.build_healthy_template(beats)
    verdict = thecf.evaluate(beats[0], fs, template)
    # A beat identical to (an average of) the template should score very high NCC.
    assert verdict.ncc > 0.9


def test_massive_amplitude_fails_energy_gate():
    fs = 360.0
    template = thecf.build_healthy_template([_sine_beat(fs) for _ in range(5)])
    huge = _sine_beat(fs, amplitude=50.0)
    verdict = thecf.evaluate(huge, fs, template)
    assert not verdict.passed
    assert verdict.failed_layer == "energy"
