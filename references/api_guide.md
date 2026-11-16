# Q6 数据说明

## 输入

`run()` 接收：

| 字段 | 类型 | 必需字段 |
|---|---|---|
| `cta_returns` | DataFrame | `date` + 18 个品种列（RB…FG） |
| `margin` | DataFrame / Series | `product` / `margin_rate`，或按品种索引的 Series |

不传 `input_data` 时读取随仓库携带的基线。

## 冻结基线

`references/baseline/`：

| 文件 | 内容 | 来源 |
|---|---|---|
| `cta_returns.parquet` | date + 18 品种逐日收益 + 组合 `ret` | Q2 固定日期换月 |
| `margin.parquet` | product / margin_rate | Q2 合约信息，按品种取主力合约中位数 |

重新生成：

```bash
python scripts/prepare_baseline.py /path/to/q2-roll-cta
```

## 口径

- 收益按每品种 100 万名义资金归一（Q2 `equity_fixed.csv` 分品种盈亏 / 1,000,000）
- 组合层只改权重，不改信号、不改换月规则
- 月度再平衡：每月首个交易日，用之前 60 个交易日估计协方差
- 成本：按权重变化计双边 1.5bp
- 保证金占用 = Σ |权重| × 品种保证金率；杠杆 = Σ |权重|
- 波动率目标先触发杠杆上限 1.5，保证金上限 60% 未绑定
- 不使用随机数或模拟收益

## 调用限制

- 历史窗口不足 20 天时退化为等权 + 对角协方差，并在结果中体现
- 协方差估计使用样本协方差 × 252，加 1e-8 对角线防奇异
- ERC 用 SLSQP 求解，失败时回退到逆波动率权重
