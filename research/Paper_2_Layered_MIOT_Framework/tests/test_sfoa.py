import numpy as np

from Common import sfoa


def test_sfoa_minimizes_simple_quadratic():
    # minimize (x-3)^2 + (y+2)^2 over a box that contains the optimum
    result = sfoa.minimize(
        lambda p: (p[0] - 3) ** 2 + (p[1] + 2) ** 2,
        bounds=[(-10, 10), (-10, 10)],
        population=20, iterations=30, seed=1,
    )
    assert result.best_score < 0.5
    assert abs(result.best_params[0] - 3) < 1.0
    assert abs(result.best_params[1] + 2) < 1.0
    assert len(result.history) == 30
    # history should be monotonically non-increasing (best-so-far)
    assert all(a >= b for a, b in zip(result.history, result.history[1:]))
