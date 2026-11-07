"""Hybrid GAN-SVM-DT edge-layer anomaly detector, SFOA-tuned.

The paper's "HGAN" is not a conventional neural GAN: an SVM plays the "generator" role
(produces the normal/abnormal decision boundary) and a DT plays the "discriminator" role
(flags the SVM's misclassifications), with SFOA tuning both sets of hyperparameters jointly
against a combined objective (Eq. 4: maximize SVM accuracy, minimize DT's detected error
rate). This is implemented exactly as described — SVM + DT, SFOA-tuned, not swapped for a
standard neural GAN — flagged here (and in research/FEASIBILITY_REPORT.md section 15) as a
notable, non-standard design choice in the *original* paper, not something this
reproduction simplified away.

Final decision combines both models as a confidence-weighted vote; the vote weight itself is
part of what SFOA tunes, which is how the "DT catches SVM's errors" idea turns into something
that actually changes the output rather than only being measured after the fact.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from Common import sfoa

# SFOA search space: [log10(C), log10(gamma), dt_max_depth, dt_criterion_switch, svm_vote_weight]
PARAM_BOUNDS = [
    (-2.0, 3.0),   # log10(C) in [0.01, 1000]
    (-4.0, 1.0),   # log10(gamma) in [1e-4, 10]
    (2.0, 20.0),   # DT max_depth
    (0.0, 1.0),    # < 0.5 -> gini, >= 0.5 -> entropy
    (0.3, 0.9),    # weight given to SVM in the final vote (DT gets 1 - weight)
]

DEFAULT_PARAMS = np.array([0.0, -1.0, 8.0, 0.0, 0.6])  # C=1, gamma=0.1, depth=8, gini, 0.6


@dataclass
class HGANSVMDT:
    svm: SVC
    dt: DecisionTreeClassifier
    svm_weight: float

    @classmethod
    def from_params(cls, params: np.ndarray) -> "HGANSVMDT":
        log_c, log_gamma, max_depth, criterion_switch, svm_weight = params
        svm = SVC(
            C=10 ** log_c, gamma=10 ** log_gamma, kernel="rbf", probability=True,
            random_state=0,
        )
        dt = DecisionTreeClassifier(
            max_depth=max(2, int(round(max_depth))),
            criterion="entropy" if criterion_switch >= 0.5 else "gini",
            random_state=0,
        )
        return cls(svm=svm, dt=dt, svm_weight=float(np.clip(svm_weight, 0.0, 1.0)))

    def fit(self, X: np.ndarray, y: np.ndarray) -> "HGANSVMDT":
        self.svm.fit(X, y)
        self.dt.fit(X, y)
        return self

    def predict_proba_abnormal(self, X: np.ndarray) -> np.ndarray:
        svm_p = self.svm.predict_proba(X)[:, 1]
        dt_p = self.dt.predict_proba(X)[:, 1]
        return self.svm_weight * svm_p + (1 - self.svm_weight) * dt_p

    def predict(self, X: np.ndarray) -> np.ndarray:
        return (self.predict_proba_abnormal(X) >= 0.5).astype(int)


def _objective(params: np.ndarray, X_train, y_train, X_val, y_val) -> float:
    model = HGANSVMDT.from_params(params).fit(X_train, y_train)
    svm_acc = accuracy_score(y_val, model.svm.predict(X_val))
    dt_preds = model.dt.predict(X_val)
    svm_preds = model.svm.predict(X_val)
    dt_detected_errors = np.mean(dt_preds != svm_preds)  # DT catching SVM's mistakes
    objective = 0.7 * svm_acc - 0.3 * dt_detected_errors  # Eq. 4, alpha=0.7, beta=0.3
    return -objective  # SFOA minimizes


def train_with_sfoa(
    X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray,
    population: int = 10, iterations: int = 15, seed: int = 0,
) -> tuple[HGANSVMDT, sfoa.SFOAResult]:
    """SFOA-tuned HGAN-SVM-DT. Scoped-down population/iterations (10/15) vs. the paper's
    30/50 by default — see research/FEASIBILITY_REPORT.md compute-budget note; pass larger
    values for a closer-to-paper run."""
    result = sfoa.minimize(
        lambda p: _objective(p, X_train, y_train, X_val, y_val),
        bounds=PARAM_BOUNDS, population=population, iterations=iterations, seed=seed,
    )
    model = HGANSVMDT.from_params(result.best_params).fit(X_train, y_train)
    return model, result


def train_default(X_train: np.ndarray, y_train: np.ndarray) -> HGANSVMDT:
    return HGANSVMDT.from_params(DEFAULT_PARAMS).fit(X_train, y_train)
