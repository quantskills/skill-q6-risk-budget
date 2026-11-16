"""Q6 组合层风险预算引擎：等权、波动率目标、ERC。

在 Q2 冻结的商品 CTA 收益矩阵上，只改变组合层资金分配，不改信号、不改换月。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize


@dataclass(frozen=True)
class Params:
    cost_bps: float = 1.5
    target_vol: float = 0.10
    max_leverage: float = 1.5
    max_margin: float = 0.60
    lookback: int = 60


def month_starts(dates: list[str]) -> list[int]:
    marks = []
    for i, d in enumerate(dates):
        if i == 0 or d[:6] != dates[i - 1][:6]:
            marks.append(i)
    return marks


def equal_weights(n: int) -> np.ndarray:
    return np.ones(n) / n


def inverse_vol_weights(cov: np.ndarray) -> np.ndarray:
    vol = np.sqrt(np.diag(cov))
    inv = 1 / np.maximum(vol, 1e-8)
    return inv / inv.sum()


def erc_weights(cov: np.ndarray) -> np.ndarray:
    n = cov.shape[0]
    target = 1.0 / n

    def objective(w: np.ndarray) -> float:
        port_var = float(w @ cov @ w)
        if port_var <= 0:
            return 1e6
        rc = w * (cov @ w) / port_var
        return float(np.sum((rc - target) ** 2))

    w0 = inverse_vol_weights(cov)
    bounds = [(0.0, 1.0)] * n
    cons = {"type": "eq", "fun": lambda w: w.sum() - 1.0}
    res = minimize(objective, w0, method="SLSQP", bounds=bounds, constraints=cons,
                   options={"maxiter": 500, "ftol": 1e-12})
    w = res.x if res.success else w0
    w = np.clip(w, 0, None)
    return w / w.sum()


def scale_to_target(w: np.ndarray, cov: np.ndarray, margin: np.ndarray,
                    params: Params) -> np.ndarray:
    port_vol = math.sqrt(float(w @ cov @ w))
    if port_vol > 0:
        w = w * (params.target_vol / port_vol)
    lev = np.abs(w).sum()
    if lev > params.max_leverage:
        w = w * (params.max_leverage / lev)
    usage = float(np.abs(w) @ margin)
    if usage > params.max_margin:
        w = w * (params.max_margin / usage)
    return w


def simulate(rets: pd.DataFrame, margin: pd.Series, scheme: str,
             params: Params | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    params = params or Params()
    if scheme not in {"equal", "vol", "erc"}:
        raise ValueError(f"未知方案: {scheme}")
    products = list(rets.columns)
    dates = rets.index.tolist()
    r = rets.values
    m = margin.reindex(products).values
    n = len(products)
    starts = set(month_starts(dates))
    weights = np.zeros(n)
    curve, rc_rows = [], []

    for i, d in enumerate(dates):
        cost = 0.0
        cov = None
        if i in starts:
            hist = r[max(0, i - params.lookback):i]
            if len(hist) < 20:
                w = equal_weights(n)
                cov = np.diag(np.full(n, 0.01))
            else:
                cov = np.cov(hist, rowvar=False) * 252
                cov = cov + np.eye(n) * 1e-8
                if scheme == "equal":
                    w = equal_weights(n)
                elif scheme == "vol":
                    w = inverse_vol_weights(cov)
                    w = scale_to_target(w, cov, m, params)
                else:
                    w = erc_weights(cov)
                    w = scale_to_target(w, cov, m, params)
            cost = float(np.abs(w - weights).sum()) * params.cost_bps / 10000
            weights = w
            if scheme != "equal" and cov is not None:
                port_var = float(weights @ cov @ weights)
                rc = weights * (cov @ weights) / port_var if port_var > 0 else np.zeros(n)
            else:
                rc = np.full(n, 1.0 / n)
            for k, p in enumerate(products):
                rc_rows.append({"date": d, "scheme": scheme, "product": p,
                                "weight": float(weights[k]),
                                "risk_contrib": float(rc[k])})

        port_ret = float(weights @ r[i]) - cost
        curve.append({"date": d, "ret": port_ret, "cost": cost,
                      "leverage": float(np.abs(weights).sum()),
                      "margin_usage": float(np.abs(weights) @ m)})

    return pd.DataFrame(curve), pd.DataFrame(rc_rows)


def metrics(df: pd.DataFrame, name: str, params: Params | None = None) -> dict:
    params = params or Params()
    ret = df["ret"]
    years = len(ret) / 252
    total = float((1 + ret).prod() - 1)
    ann = (1 + total) ** (1 / years) - 1 if years > 0 else 0
    vol = float(ret.std() * math.sqrt(252))
    curve = (1 + ret).cumprod()
    mdd = float((curve / curve.cummax() - 1).min())
    return {
        "scheme": name,
        "total_return": round(total, 4),
        "annual_return": round(ann, 4),
        "annual_vol": round(vol, 4),
        "sharpe": round(ann / vol, 3) if vol else None,
        "max_drawdown": round(mdd, 4),
        "calmar": round(ann / abs(mdd), 3) if mdd else None,
        "turnover_x": round(float(df["cost"].sum() / (params.cost_bps / 10000) / years), 2),
        "avg_leverage": round(float(df["leverage"].mean()), 3),
        "max_margin_usage": round(float(df["margin_usage"].max()), 3),
        "avg_margin_usage": round(float(df["margin_usage"].mean()), 3),
        "total_cost": round(float(df["cost"].sum()), 4),
    }
