"""Q6 BUILD 测试：输入校验、三套配置、确定性与生产字段。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build  # noqa: E402
import data as data_layer  # noqa: E402
import engine  # noqa: E402

START = "20210104"
END = "20221231"


def baseline_frames() -> dict:
    rets, margin = data_layer.load_baseline()
    returns = rets.reset_index().rename(columns={"index": "date"})
    margin_frame = margin.rename("margin_rate").reset_index()
    margin_frame.columns = ["product", "margin_rate"]
    return {"cta_returns": returns, "margin": margin_frame}


class ValidateInputTest(unittest.TestCase):
    def test_none_is_allowed(self):
        build.validate_input(None)

    def test_rejects_non_dict(self):
        with self.assertRaises(TypeError):
            build.validate_input([1, 2])

    def test_rejects_missing_key(self):
        with self.assertRaises(ValueError):
            build.validate_input({"cta_returns": pd.DataFrame()})

    def test_rejects_empty(self):
        frames = baseline_frames()
        frames["margin"] = frames["margin"].iloc[0:0]
        with self.assertRaises(ValueError):
            build.validate_input(frames)

    def test_rejects_missing_columns(self):
        frames = baseline_frames()
        frames["cta_returns"] = frames["cta_returns"].drop(columns=["RB"])
        with self.assertRaises(ValueError):
            build.validate_input(frames)


class ConfigTest(unittest.TestCase):
    def test_rejects_bad_scheme(self):
        with self.assertRaises(ValueError):
            build.run(None, {"schemes": ["momentum"]})

    def test_rejects_unknown_key(self):
        with self.assertRaises(ValueError):
            build.run(None, {"foo": 1})

    def test_rejects_short_lookback(self):
        with self.assertRaises(ValueError):
            build.run(None, {"lookback": 5})


class RunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = build.run(None, {"start_date": START, "end_date": END})

    def test_three_schemes(self):
        names = [row["scheme"] for row in self.result["metrics"]]
        self.assertEqual(names, ["equal", "vol", "erc"])

    def test_metrics_keys(self):
        for row in self.result["metrics"]:
            for key in ("annual_return", "annual_vol", "sharpe", "max_drawdown",
                        "turnover_x", "avg_leverage", "max_margin_usage"):
                self.assertIn(key, row)

    def test_equity_not_empty(self):
        for scheme in ("equal", "vol", "erc"):
            self.assertGreater(len(self.result["equity"][scheme]), 200)

    def test_risk_contrib(self):
        rc = self.result["risk_contrib"]
        self.assertFalse(rc.empty)
        for scheme in ("vol", "erc"):
            sub = rc[rc["scheme"] == scheme]
            self.assertGreater(len(sub), 0)
            self.assertTrue((sub["weight"].dropna() >= -1e-9).all())

    def test_production_schema(self):
        frame = build.to_production(self.result)
        expected = {"trade_date", "build_id", "build_name", "target_id",
                    "result_type", "result_value", "result_json",
                    "data_version", "update_time"}
        self.assertEqual(set(frame.columns), expected)
        self.assertEqual(len(frame), 3)
        self.assertEqual(build.BUILD_ID, "Q6")

    def test_deterministic(self):
        again = build.run(None, {"start_date": START, "end_date": END})
        self.assertEqual(self.result["metrics"], again["metrics"])


class ErcTest(unittest.TestCase):
    def test_weights_sum_to_one(self):
        rets, _ = data_layer.load_baseline()
        slice_ = rets.iloc[:60]
        cov = np.cov(slice_.values, rowvar=False) * 252 + np.eye(len(slice_.columns)) * 1e-8
        w = engine.erc_weights(cov)
        self.assertAlmostEqual(float(w.sum()), 1.0, places=6)
        self.assertTrue((w >= 0).all())


if __name__ == "__main__":
    unittest.main(verbosity=2)
