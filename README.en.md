# CTA Portfolio Risk-Budget Skill

**English** | [简体中文](README.md)

> Same frozen CTA signal, only the portfolio layer changes: equal weight, volatility targeting, and ERC. Does risk budgeting improve after-cost performance, or just cut the return source?

<p align="center">
  <img alt="schemes" src="https://img.shields.io/badge/schemes-equal%20%7C%20vol%20%7C%20ERC-blue">
  <img alt="data source" src="https://img.shields.io/badge/data-PandaData-ff69b4">
  <img alt="build" src="https://img.shields.io/badge/BUILD-Q6-7c3aed">
</p>

---

## What it is

`risk-budget` is a **BUILD skill** (Q6). On the frozen Q2 commodity CTA return matrix, it changes only the portfolio weights and compares:

| Scheme | Weights | Scaling |
|---|---|---|
| `equal` | 1/18 per product | None, leverage 1.0 |
| `vol` | Inverse 60-day volatility | 10% annual vol target, leverage cap 1.5, margin cap 60% |
| `erc` | Equal risk contribution via 60-day covariance | Same vol target and caps |

Monthly rebalancing on the first trading day, using the prior 60 trading days; turnover costs 1.5 bp per side.

## Results (2021-01-04 to 2025-12-31)

| Scheme | Total | Annual | Vol | Sharpe | Max DD | Turnover | Avg leverage | Margin (avg/peak) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Equal | **6.25%** | **1.27%** | 11.18% | **0.113** | -22.19% | 0.21x | 1.00 | 20.0% / 20.0% |
| Vol target (10%) | 2.54% | 0.52% | 10.84% | 0.048 | **-16.54%** | 2.58x | 1.31 | 26.1% / 30.0% |
| ERC | -0.95% | -0.20% | 10.69% | -0.019 | -19.27% | 5.04x | 1.34 | 26.9% / 30.0% |

**Key finding: risk budgeting did not improve after-cost performance.** Equal weight has the best return and risk-adjusted result. Vol targeting cuts drawdown to -16.5% but costs 0.75 pp of annual return and lifts turnover to 2.58x; ERC turns negative. The Q2 return is concentrated in high-volatility trend products (JM/AG/AU), and risk scaling moves weight away from the return source.

## Quick start

```bash
pip install -r requirements.txt
python scripts/build.py --write-production
python scripts/test.py
```

## Production parquet fields

| Field | Description |
|---|---|
| `trade_date` | Result trading date |
| `build_id` | `Q6` |
| `build_name` | `risk-budget` |
| `target_id` | Scheme (`equal` / `vol` / `erc`) |
| `result_type` | `report` |
| `result_value` | Annualized return |
| `result_json` | Full metrics and stress months |
| `data_version` | Data version |
| `update_time` | Generation timestamp |

## Data

- Frozen CTA returns: Q2 fixed-date rolls, 18 commodity products, 2021-01-04 to 2025-12-31
- Margin rates: median main-contract margin per product from Q2 contract metadata
- Execution: monthly rebalance, 1.5 bp per side on weight changes
- No random or simulated returns

## Limitations

- Risk budgeting depends on the correlation structure; in stress periods commodities move together and ERC diversification fails
- Results are sensitive to covariance window, vol target, and leverage/margin caps
- No capacity, market-impact, or liquidity modeling
- Research and education only, not investment advice

## ⚠️ Disclaimer

- Research and education only. **Not investment advice.** No return is promised.
- Backtests rely on historical data and explicit assumptions; future results may differ materially.
- This is a QuantSkills community project, **not officially endorsed by PandaAI**.
- Verify data, parameters, costs, and risk boundaries before use.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
