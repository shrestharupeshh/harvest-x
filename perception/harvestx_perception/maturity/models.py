"""Maturity classifiers: a transparent single-feature rule baseline and classical ML.

The learned models must beat the rule baseline on held-out *plants* (grouped split)
to justify their extra complexity.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ..synthetic.growth import MATURITY_CLASSES


class SizeRuleBaseline:
    """Ordered thresholds on one size feature (e.g. canopy diameter).

    Thresholds are the midpoints between medians of adjacent classes in the training
    set. Predictions are hard (probability 1 for the chosen class), which is exactly
    what a fixed "harvest when the head is X cm wide" rule does.
    """

    def __init__(self, feature: str):
        self.feature_names = [feature]
        self.classes_ = np.array(MATURITY_CLASSES)
        self.thresholds_: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> SizeRuleBaseline:
        x = np.asarray(X, float).reshape(len(y), -1)[:, 0]
        med = []
        for c in MATURITY_CLASSES:
            v = x[(np.asarray(y) == c) & np.isfinite(x)]
            med.append(np.median(v) if len(v) else np.nan)
        med = np.array(med)
        # fill missing classes by interpolation, enforce monotonic order
        idx = np.arange(len(med))
        ok = np.isfinite(med)
        med = np.interp(idx, idx[ok], med[ok])
        med = np.maximum.accumulate(med)
        self.thresholds_ = (med[:-1] + med[1:]) / 2
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        x = np.nan_to_num(np.asarray(X, float).reshape(len(X), -1)[:, 0], nan=0.0)
        return self.classes_[np.searchsorted(self.thresholds_, x, side="right")]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        pred = self.predict(X)
        return (pred[:, None] == self.classes_[None, :]).astype(float)


class FeatureModel:
    """sklearn pipeline bundled with the feature names it expects."""

    def __init__(self, kind: str, feature_names: list[str], seed: int = 0):
        self.kind, self.feature_names = kind, list(feature_names)
        if kind == "logreg":
            est = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                LogisticRegression(max_iter=2000, class_weight="balanced"))
        elif kind == "rf":
            est = make_pipeline(
                SimpleImputer(strategy="median"),
                RandomForestClassifier(n_estimators=300, min_samples_leaf=3,
                                       class_weight="balanced", random_state=seed, n_jobs=1),
            )
        else:
            raise ValueError(kind)
        self.est = est

    def fit(self, X, y):
        self.est.fit(X, y)
        self.classes_ = self.est.classes_
        return self

    def predict(self, X):
        return self.est.predict(X)

    def predict_proba(self, X):
        return self.est.predict_proba(X)


def mass_regressor(seed: int = 0):
    return make_pipeline(
        SimpleImputer(strategy="median"),
        RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=seed, n_jobs=-1),
    )
