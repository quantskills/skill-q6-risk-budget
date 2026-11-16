---
name: risk-budget-production
description: 生产环境的 CTA 组合风险预算结果读取。从标准 Parquet 读取等权、波动率目标与 ERC 的扣费后指标与压力月份。
tags: [quant, build, production, futures, risk-budget]
---

# CTA 组合风险预算（生产）

## 结果文件

`生产产物/数据库.parquet`

## 主键

- `trade_date`
- `build_id`
- `target_id`
- `result_type`

## 字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `trade_date` | string | 结果所属交易日 YYYYMMDD |
| `build_id` | string | `Q6` |
| `build_name` | string | `risk-budget` |
| `target_id` | string | 方案：`equal` / `vol` / `erc` |
| `result_type` | string | `report` |
| `result_value` | float | 年化收益（小数） |
| `result_json` | string | 完整指标与压力月份 JSON |
| `data_version` | string | 数据版本 |
| `update_time` | string | 生成时间 |

## 读取规则

```python
import json
import pandas as pd

df = pd.read_parquet("生产产物/数据库.parquet")
latest = df[df["trade_date"] == df["trade_date"].max()]
equal = latest[latest["target_id"] == "equal"].iloc[0]
detail = json.loads(equal["result_json"])
print(equal["result_value"], detail["sharpe"], detail["turnover_x"])
```

1. 先按 `trade_date` 取最新有效交易日。
2. 再按 `target_id` 取方案。
3. `result_value` 只作核心指标；完整口径以 `result_json` 为准。
4. 最新结果缺失时说明数据日期，不允许用开发脚本临时重算替代。

## 禁止行为

- 不得把 `result_value` 当作收益承诺或配置建议
- 不得修改 `result_json` 后回写
- 不得在缺少 `trade_date` / `build_id` / `target_id` 时合并数据
