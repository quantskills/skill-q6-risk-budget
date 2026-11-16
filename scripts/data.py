"""Q6 数据层：冻结 CTA 基线（收益 + 保证金率）。

基线来自 Q2 真实数据快照，随仓库携带；也可用 input_data 传入自定义矩阵。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PRODUCTS = ["RB", "HC", "I", "J", "JM", "CU", "AL", "ZN", "AU", "AG", "RU",
            "M", "Y", "P", "C", "TA", "MA", "FG"]
BASELINE_DIR = Path(__file__).resolve().parent.parent / "references" / "baseline"


def load_baseline(base_dir: str | Path | None = None) -> tuple[pd.DataFrame, pd.Series]:
    base = Path(base_dir) if base_dir else BASELINE_DIR
    returns = pd.read_parquet(base / "cta_returns.parquet")
    margin = pd.read_parquet(base / "margin.parquet")
    returns["date"] = returns["date"].astype(str)
    rets = returns.set_index("date")[PRODUCTS].astype(float)
    margin_series = (margin.set_index("product")["margin_rate"]
                     .reindex(PRODUCTS).astype(float))
    if margin_series.isna().any():
        raise ValueError("保证金率基线缺少品种，请检查 references/baseline/margin.parquet")
    return rets, margin_series


def load_local(data_dir: str | Path) -> tuple[pd.DataFrame, pd.Series]:
    base = Path(data_dir)
    returns = pd.read_parquet(base / "cta_returns.parquet")
    margin = pd.read_parquet(base / "margin.parquet")
    returns["date"] = returns["date"].astype(str)
    rets = returns.set_index("date")[PRODUCTS].astype(float)
    margin_series = (margin.set_index("product")["margin_rate"]
                     .reindex(PRODUCTS).astype(float))
    return rets, margin_series
