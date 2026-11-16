"""从 Q2 项目导出 Q6 共用基线（真实数据快照）。

用法：
    python scripts/prepare_baseline.py <q2_project_dir>

输出：
    references/baseline/cta_returns.parquet
    references/baseline/margin.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRODUCTS = ["RB", "HC", "I", "J", "JM", "CU", "AL", "ZN", "AU", "AG", "RU",
            "M", "Y", "P", "C", "TA", "MA", "FG"]
CAPITAL_PER_PRODUCT = 1_000_000.0


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("用法: python scripts/prepare_baseline.py <q2_project_dir>")
    src = Path(sys.argv[1])
    out = Path(__file__).resolve().parent.parent / "references" / "baseline"
    out.mkdir(parents=True, exist_ok=True)

    eq = pd.read_csv(src / "outputs" / "equity_fixed.csv")
    eq["date"] = eq["date"].astype(str)
    rets = eq[["date", "ret"] + PRODUCTS].copy()
    for p in PRODUCTS:
        rets[p] = rets[p] / CAPITAL_PER_PRODUCT
    rets.to_parquet(out / "cta_returns.parquet", index=False)

    contracts = pd.read_parquet(src / "data" / "contracts.parquet")
    dominant = pd.read_parquet(src / "data" / "dominant.parquet")
    dominant["date"] = dominant["date"].astype(str)
    merged = dominant[dominant["underlying_symbol"].isin(PRODUCTS)].merge(
        contracts[["symbol", "margin_rate"]], on="symbol", how="left")
    margin = (merged.groupby("underlying_symbol")["margin_rate"].median()
              .reindex(PRODUCTS).fillna(0.10).rename("margin_rate").reset_index())
    margin.columns = ["product", "margin_rate"]
    margin.to_parquet(out / "margin.parquet", index=False)
    print("cta_returns", rets.shape, "margin", margin.shape, "->", out)


if __name__ == "__main__":
    main()
