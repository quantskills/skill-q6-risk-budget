"""Q6 CTA 组合风险预算 BUILD。

标准入口：
    run(input_data, config=None) -> dict
    validate_input(input_data) -> None

在冻结 CTA 收益矩阵上比较等权、波动率目标、ERC 三套资金分配。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import data as data_layer  # noqa: E402
import engine  # noqa: E402

BUILD_ID = "Q6"
BUILD_NAME = "risk-budget"
PRODUCTS = data_layer.PRODUCTS
SCHEMES = ("equal", "vol", "erc")
CONFIG_KEYS = {
    "baseline_dir", "start_date", "end_date", "schemes", "cost_bps",
    "target_vol", "max_leverage", "max_margin", "lookback",
    "output_dir", "write_production",
}


def validate_input(input_data) -> None:
    if input_data is None:
        return
    if not isinstance(input_data, dict):
        raise TypeError("input_data 必须是 dict 或 None")
    unknown = set(input_data) - {"cta_returns", "margin"}
    if unknown:
        raise ValueError(f"input_data 含未知字段: {sorted(unknown)}")
    for key in ("cta_returns", "margin"):
        if key not in input_data:
            raise ValueError(f"input_data 缺少字段: {key}")
        value = input_data[key]
        if isinstance(value, pd.Series) and key == "margin":
            if value.empty:
                raise ValueError("margin 不能为空")
            continue
        if not isinstance(value, pd.DataFrame) or value.empty:
            raise ValueError(f"input_data['{key}'] 必须是非空 DataFrame")
    rets = input_data["cta_returns"]
    missing = {"date"} | set(PRODUCTS)
    missing -= set(rets.columns)
    if missing:
        raise ValueError(f"cta_returns 缺少字段: {sorted(missing)}")
    if isinstance(input_data["margin"], pd.DataFrame):
        missing = {"product", "margin_rate"} - set(input_data["margin"].columns)
        if missing:
            raise ValueError(f"margin 缺少字段: {sorted(missing)}")


def _validate_config(config: dict | None) -> dict:
    if config is None:
        config = {}
    if not isinstance(config, dict):
        raise TypeError("config 必须是 dict 或 None")
    unknown = set(config) - CONFIG_KEYS
    if unknown:
        raise ValueError(f"config 含未知字段: {sorted(unknown)}")
    cfg = {
        "baseline_dir": None,
        "start_date": "20210104",
        "end_date": "20251231",
        "schemes": list(SCHEMES),
        "cost_bps": 1.5,
        "target_vol": 0.10,
        "max_leverage": 1.5,
        "max_margin": 0.60,
        "lookback": 60,
        "output_dir": None,
        "write_production": False,
    }
    cfg.update(config)
    for key in ("start_date", "end_date"):
        value = str(cfg[key])
        if len(value) != 8 or not value.isdigit():
            raise ValueError(f"{key} 必须是 YYYYMMDD")
        cfg[key] = value
    if cfg["start_date"] > cfg["end_date"]:
        raise ValueError("start_date 不能晚于 end_date")
    bad = set(cfg["schemes"]) - set(SCHEMES)
    if bad or not cfg["schemes"]:
        raise ValueError(f"schemes 只能取 {SCHEMES} 的子集")
    cfg["schemes"] = list(dict.fromkeys(cfg["schemes"]))
    for key in ("cost_bps", "target_vol", "max_leverage", "max_margin"):
        if not isinstance(cfg[key], (int, float)) or cfg[key] <= 0:
            raise ValueError(f"{key} 必须是正数")
    if cfg["max_leverage"] < 1:
        raise ValueError("max_leverage 不能小于 1")
    if not isinstance(cfg["lookback"], int) or cfg["lookback"] < 20:
        raise ValueError("lookback 必须 >= 20")
    return cfg


def _params(cfg: dict) -> engine.Params:
    return engine.Params(
        cost_bps=float(cfg["cost_bps"]),
        target_vol=float(cfg["target_vol"]),
        max_leverage=float(cfg["max_leverage"]),
        max_margin=float(cfg["max_margin"]),
        lookback=int(cfg["lookback"]),
    )


def _resolve(input_data, cfg: dict):
    if input_data:
        rets = input_data["cta_returns"]
        margin = input_data["margin"]
    else:
        rets, margin = data_layer.load_baseline(cfg["baseline_dir"])
    returns = rets.copy()
    if "date" in returns.columns:
        returns["date"] = returns["date"].astype(str)
        returns = returns.set_index("date")
    else:
        returns.index = returns.index.astype(str)
    if isinstance(margin, pd.DataFrame):
        margin = margin.set_index("product")["margin_rate"]
    margin = margin.reindex(PRODUCTS).astype(float)
    if margin.isna().any():
        raise ValueError("保证金率缺少品种")
    return returns[PRODUCTS].astype(float), margin


def run(input_data=None, config: dict | None = None) -> dict:
    validate_input(input_data)
    cfg = _validate_config(config)
    rets, margin = _resolve(input_data, cfg)
    dates = [d for d in rets.index if cfg["start_date"] <= d <= cfg["end_date"]]
    if len(dates) < 60:
        raise ValueError("回测区间交易日不足 60 天")
    rets = rets.loc[dates]

    params = _params(cfg)
    metrics_rows, curves, rc_frames, yearly, stress = [], {}, [], [], {}
    for scheme in cfg["schemes"]:
        curve, rc = engine.simulate(rets, margin, scheme, params)
        curves[scheme] = curve
        if not rc.empty:
            rc_frames.append(rc)
        metrics_rows.append(engine.metrics(curve, scheme, params))
        frame = curve.copy()
        frame["year"] = frame["date"].str[:4]
        for year, grp in frame.groupby("year"):
            yearly.append({"scheme": scheme, "year": year,
                           "return": round(float((1 + grp["ret"]).prod() - 1), 4)})
        bad = frame.copy()
        bad["month"] = bad["date"].str[:6]
        worst = (bad.groupby("month")["ret"].apply(lambda x: (1 + x).prod() - 1)
                 .sort_values().head(5))
        stress[scheme] = [{"month": k, "ret": round(float(v), 4)} for k, v in worst.items()]

    result = {
        "metrics": metrics_rows,
        "yearly": yearly,
        "stress_months": stress,
        "risk_contrib": pd.concat(rc_frames, ignore_index=True) if rc_frames else pd.DataFrame(),
        "equity": curves,
        "data_version": f"pandadata-cta:{dates[0]}..{dates[-1]}",
        "config": cfg,
    }
    if cfg["output_dir"]:
        _write_outputs(result, Path(cfg["output_dir"]))
    if cfg["write_production"]:
        write_production(result, Path(__file__).resolve().parent.parent / "生产产物")
    return result


def _write_outputs(result: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(result["metrics"]).to_csv(out / "metrics.csv", index=False)
    pd.DataFrame(result["yearly"]).to_csv(out / "yearly_returns.csv", index=False)
    for scheme, frame in result["equity"].items():
        frame.to_csv(out / f"equity_{scheme}.csv", index=False)
    if not result["risk_contrib"].empty:
        result["risk_contrib"].to_csv(out / "risk_contrib.csv", index=False)
    (out / "stress_months.json").write_text(
        json.dumps(result["stress_months"], ensure_ascii=False, indent=2), encoding="utf-8")


def to_production(result: dict) -> pd.DataFrame:
    last_date = str(result["equity"][result["config"]["schemes"][0]]["date"].max())
    update_time = datetime.now().astimezone().isoformat(timespec="seconds")
    rows = []
    for row in result["metrics"]:
        detail = dict(row)
        detail["stress_months"] = result["stress_months"].get(row["scheme"], [])
        rows.append({
            "trade_date": last_date,
            "build_id": BUILD_ID,
            "build_name": BUILD_NAME,
            "target_id": row["scheme"],
            "result_type": "report",
            "result_value": float(row.get("annual_return") or 0.0),
            "result_json": json.dumps(detail, ensure_ascii=False),
            "data_version": result["data_version"],
            "update_time": update_time,
        })
    return pd.DataFrame(rows)


def write_production(result: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    frame = to_production(result)
    path = out_dir / "数据库.parquet"
    frame.to_parquet(path, index=False)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Q6 CTA 组合风险预算 BUILD")
    parser.add_argument("--baseline-dir", default=None)
    parser.add_argument("--start", default="20210104")
    parser.add_argument("--end", default="20251231")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--schemes", nargs="*", default=None)
    parser.add_argument("--write-production", action="store_true")
    args = parser.parse_args()
    result = run(None, {
        "baseline_dir": args.baseline_dir,
        "start_date": args.start,
        "end_date": args.end,
        "schemes": args.schemes or list(SCHEMES),
        "output_dir": args.output_dir,
        "write_production": args.write_production,
    })
    print(pd.DataFrame(result["metrics"]).to_string(index=False))


if __name__ == "__main__":
    main()
