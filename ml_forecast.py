"""Lightweight autoregressive forecasting utilities for the Cloudy&Shiny Index.

Avoids heavy dependencies (statsmodels/prophet). Uses ordinary least squares
to fit an AR(p) model with optional ridge regularization for numerical stability.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import numpy as np


@dataclass
class ARModel:
    order: int
    coef: np.ndarray  # shape (order,)
    intercept: float
    sigma: float      # residual std
    rmse: float
    r2: float

    def forecast(self, history: List[float], steps: int = 1) -> List[float]:
        vals = list(history)
        out = []
        for _ in range(steps):
            if len(vals) < self.order:
                # fallback to last value if insufficient
                out.append(vals[-1])
                vals.append(vals[-1])
                continue
            lag_vector = np.array(vals[-self.order:][::-1])  # most recent first reversed to match coef order
            y_hat = self.intercept + float(np.dot(self.coef, lag_vector))
            # clamp to 0-100 domain of index
            y_hat = max(0.0, min(100.0, y_hat))
            out.append(y_hat)
            vals.append(y_hat)
        return out


def fit_ar(series: List[float], max_order: int = 10, ridge_lambda: float = 0.0) -> ARModel | None:
    y = np.asarray(series, dtype=float)
    n = len(y)
    if n < 8:  # need enough points
        return None
    best_aic = float('inf')
    best: ARModel | None = None
    for p in range(2, min(max_order, n - 2) + 1):
        # Construct design matrix: rows n-p, cols p (lags), plus intercept
        rows = n - p
        X = np.zeros((rows, p))
        for i in range(rows):
            X[i, :] = y[i + (p - 1)::-1][:p]  # last p values preceding target
        target = y[p:]
        # Add ridge regularization
        XtX = X.T @ X
        if ridge_lambda > 0:
            XtX += ridge_lambda * np.eye(p)
        try:
            coef = np.linalg.solve(XtX, X.T @ target)
        except np.linalg.LinAlgError:
            continue
        intercept = float(target.mean() - X.mean(axis=0) @ coef)
        preds = intercept + X @ coef
        resid = target - preds
        sigma = float(np.sqrt(np.mean(resid ** 2)))
        # AIC for AR(p): 2k + n*ln(RSS/n)
        rss = float(np.sum(resid ** 2))
        k = p + 1
        aic = 2 * k + rows * np.log(rss / rows + 1e-12)
        if aic < best_aic:
            ss_tot = float(np.sum((target - target.mean()) ** 2)) or 1e-9
            r2 = 1 - rss / ss_tot
            best_aic = aic
            best = ARModel(order=p, coef=coef, intercept=intercept, sigma=sigma, rmse=sigma, r2=r2)
    return best


def advanced_forecast(history: List[float], steps: int = 1) -> Dict:
    model = fit_ar(history)
    if not model:
        return {"model": "fallback-naive", "prediction": history[-1], "rmse": None, "r2": None, "order": None}
    preds = model.forecast(history, steps=steps)
    # Provide first-step prediction + basic conf interval (approx 1.96*sigma)
    pred1 = preds[0]
    ci = 1.96 * model.sigma
    return {
        "model": f"AR({model.order})",
        "prediction": round(pred1, 2),
        "lower": round(max(0.0, pred1 - ci), 2),
        "upper": round(min(100.0, pred1 + ci), 2),
        "rmse": round(model.rmse, 4),
        "r2": round(model.r2, 4),
        "order": model.order
    }
