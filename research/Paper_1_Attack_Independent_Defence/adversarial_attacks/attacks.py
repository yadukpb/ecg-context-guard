"""FGSM / PGD (white-box) and HopSkipJump / Boundary (black-box) attacks.

FGSM and PGD are implemented directly from the paper's own Eq. 2-3 against the trained
PyTorch model (gradient-based, genuine white-box attacks, not simplified).

HopSkipJump and Boundary are now wired up via IBM's `adversarial-robustness-toolbox` (ART,
installed cleanly into Common/venv — no dependency conflicts with the pinned torch==2.4.1
after all), using ART's real `HopSkipJumpAttack`/`BoundaryAttack` against the trained model
wrapped in `PyTorchClassifier`. `max_iter`/`max_eval` are kept modest (not ART's defaults,
which assume a much larger query budget) so a handful of samples finishes in a bounded time
on CPU — this is a scope choice (fewer queries per sample), not a different algorithm.

`simplified_boundary_walk` below is kept as the ORIGINAL fallback from before ART was
installed: genuinely black-box (uses only the model's output class, no gradients), but it is
NOT IBM ART's HopSkipJump or Boundary attack and must never be reported as such — report it
as "simplified boundary-walk (fallback, pre-ART)" if it's used instead of the real ART
attacks.
"""
from __future__ import annotations

import numpy as np
import torch


def fgsm_attack(model: torch.nn.Module, x: torch.Tensor, y: torch.Tensor, epsilon: float) -> torch.Tensor:
    """Eq. 2: ECG_adv = ECG_raw + epsilon * sign(grad_loss)."""
    x = x.clone().detach().requires_grad_(True)
    loss = torch.nn.functional.cross_entropy(model(x), y)
    loss.backward()
    return (x + epsilon * x.grad.sign()).detach()


def pgd_attack(
    model: torch.nn.Module, x: torch.Tensor, y: torch.Tensor, epsilon: float,
    iterations: int = 10, alpha: float | None = None,
) -> torch.Tensor:
    """Eq. 3: iterative FGSM clipped to an epsilon ball around the original input."""
    alpha = alpha if alpha is not None else epsilon / max(1, iterations) * 2
    x_orig = x.clone().detach()
    x_adv = x.clone().detach()
    for _ in range(iterations):
        x_adv.requires_grad_(True)
        loss = torch.nn.functional.cross_entropy(model(x_adv), y)
        grad = torch.autograd.grad(loss, x_adv)[0]
        x_adv = x_adv.detach() + alpha * grad.sign()
        x_adv = torch.clamp(x_adv, x_orig - epsilon, x_orig + epsilon).detach()
    return x_adv


def _predict_class(model: torch.nn.Module, x: torch.Tensor) -> int:
    with torch.no_grad():
        return int(model(x).argmax(dim=1).item())


def simplified_boundary_walk(
    model: torch.nn.Module, x: torch.Tensor, original_class: int, epsilon: float,
    max_queries: int = 200, seed: int = 0,
) -> torch.Tensor:
    """Black-box, score-based (final class label only). Random search for a
    differently-classified start point, binary search toward the original to approach the
    boundary, then a bounded random perturbation scaled by ``epsilon`` — a simplified stand-in
    for HopSkipJump/Boundary-style attacks (see module docstring)."""
    rng = np.random.default_rng(seed)
    x_np = x.detach().numpy().copy()
    queries_used = 0

    adv = x_np + rng.normal(scale=epsilon * 5, size=x_np.shape)
    adv_t = torch.tensor(adv, dtype=torch.float32)
    queries_used += 1
    if _predict_class(model, adv_t) == original_class:
        return torch.tensor(x_np, dtype=torch.float32)  # couldn't flip the class in budget

    lo, hi = x_np.copy(), adv
    for _ in range(min(20, max_queries - queries_used)):
        mid = (lo + hi) / 2
        mid_t = torch.tensor(mid, dtype=torch.float32)
        queries_used += 1
        if _predict_class(model, mid_t) == original_class:
            lo = mid
        else:
            hi = mid

    direction = hi - x_np
    norm = np.linalg.norm(direction) + 1e-12
    perturbed = x_np + epsilon * direction / norm
    return torch.tensor(perturbed, dtype=torch.float32)


def _art_classifier(model: torch.nn.Module, input_length: int, num_classes: int = 2):
    """Wrap the trained ResNet-18(1D) in ART's PyTorchClassifier so ART's real attack
    implementations can query it. Imported lazily so the rest of this module (FGSM/PGD/the
    fallback) still works in an environment where ART isn't installed."""
    from art.estimators.classification import PyTorchClassifier

    return PyTorchClassifier(
        model=model,
        loss=torch.nn.CrossEntropyLoss(),
        input_shape=(1, input_length),
        nb_classes=num_classes,
        clip_values=(-10.0, 10.0),  # generous bound; ECG segments here are normalized, not pixel-range
    )


def art_hopskipjump_attack(
    model: torch.nn.Module, x: torch.Tensor, max_iter: int = 10, max_eval: int = 200, init_eval: int = 20,
) -> torch.Tensor:
    """Real IBM ART HopSkipJumpAttack (score/decision-based black-box). `max_iter`/`max_eval`
    are scoped well below ART's defaults (normally max_eval~10000) to keep a handful of
    samples bounded on CPU — see module docstring."""
    from art.attacks.evasion import HopSkipJump

    classifier = _art_classifier(model, x.shape[-1])
    attack = HopSkipJump(classifier=classifier, targeted=False, max_iter=max_iter, max_eval=max_eval, init_eval=init_eval)
    x_adv = attack.generate(x=x.detach().numpy())
    return torch.tensor(x_adv, dtype=torch.float32)


def art_boundary_attack(model: torch.nn.Module, x: torch.Tensor, max_iter: int = 100) -> torch.Tensor:
    """Real IBM ART BoundaryAttack (decision-based black-box). `max_iter` scoped down from
    ART's default (5000) for the same CPU-time-budget reason as HopSkipJump above."""
    from art.attacks.evasion import BoundaryAttack

    classifier = _art_classifier(model, x.shape[-1])
    attack = BoundaryAttack(estimator=classifier, targeted=False, max_iter=max_iter, verbose=False)
    x_adv = attack.generate(x=x.detach().numpy())
    return torch.tensor(x_adv, dtype=torch.float32)
