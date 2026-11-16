---
name: risk-budget
description: "CTA portfolio risk-budget BUILD: on a frozen commodity CTA return matrix, compares equal weight, volatility targeting, and equal-risk-contribution (ERC) allocations with monthly rebalancing, 60-day covariance, leverage and margin caps, and after-cost metrics. Use when an agent needs to test whether risk budgeting improves after-cost CTA performance, audit leverage and margin usage, compare ERC with equal weight, or reproduce the Q6 risk-budget study."
license: GPL-3.0-only
metadata:
  organization: QuantSkills
  organization_url: https://github.com/quantskills
  repository: skill-q6-risk-budget
  repository_url: https://github.com/quantskills/skill-q6-risk-budget
  project_type: skill
  collection: futures-risk-budget
  creator: fuzijun
  maintainer: fuzijun
quantSkills:
  project_type: skill
  category: tooling
  tags:
    - futures
    - cta
    - risk-budget
    - portfolio
    - pandadata
  platforms:
    - claude-code
    - codex
    - openclaw
    - cursor
  status: draft
  requires:
    - skill-q2-roll-cta
  validation_level: runnable
  maintainer_type: community
  summary_zh: "CTA 组合风险预算：在冻结信号上比较等权、波动率目标与 ERC，含杠杆/保证金上限、换手成本与样本外。"
  summary_en: "CTA portfolio risk budgeting: compares equal weight, volatility targeting, and ERC on a frozen signal with leverage/margin caps, turnover cost, and out-of-sample results."
---

# CTA 组合的风险预算能否改善扣费后的表现

Use this skill to test whether portfolio-level risk budgeting improves after-cost CTA performance.

## 工具定位
- 工具类型：研究/回测型 BUILD（结果型）
- 解决问题：只改组合层资金分配，比较等权、波动率目标、ERC 的扣费后收益与风险
- 使用对象：agent / 人工分析

## 适用场景
- 需要判断风险预算是否值得做
- 需要核对杠杆、保证金占用、换手与成本
- 需要复现 Q6 组合层对照或做样本外检查

## 输入
| 字段 | 类型 | 说明 |
|---|---|---|
| `cta_returns` | DataFrame | date + 18 品种逐日收益（按 100 万名义资金归一） |
| `margin` | DataFrame / Series | 品种保证金率（product / margin_rate） |
| `config.start_date` / `end_date` | str | 区间，YYYYMMDD |
| `config.schemes` | list[str] | `equal` / `vol` / `erc` |
| `config.cost_bps` | float | 单边成本，默认 1.5bp |
| `config.target_vol` | float | 波动率目标，默认 10% |
| `config.max_leverage` | float | 杠杆上限，默认 1.5 |
| `config.max_margin` | float | 保证金上限，默认 60% |
| `config.lookback` | int | 协方差窗口，默认 60 日 |

## 输出
| 字段 | 说明 |
|---|---|
| `metrics` | 三套方案的收益、波动、Sharpe、回撤、换手、杠杆、保证金占用 |
| `risk_contrib` | 每次再平衡的权重与风险贡献 |
| `yearly` | 年度收益 |
| `stress_months` | 每种方案最差 5 个自然月 |
| `equity` | 逐日净值、成本、杠杆、保证金占用 |
| `data_version` | 数据版本 |

## 调用方式
```python
from scripts.build import run, validate_input

validate_input(None)
result = run(None, {
    "start_date": "20210104",
    "end_date": "20251231",
    "schemes": ["equal", "vol", "erc"],
})
print(result["metrics"])
```

## 可被 Alpha 调用
- 否（组合层研究结果，不直接输出单标的信号）

## 是否需要生产结果
- 是，生成 `生产产物/数据库.parquet`（每种方案一行）

## 数据来源
- 冻结 CTA 基线来自 Q2 真实数据快照（`references/baseline/`）
- 合约保证金率来自 Q2 合约信息
- 不使用随机数或模拟收益

## 依赖
- pandas、numpy、scipy、pyarrow
