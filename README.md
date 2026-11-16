# CTA 组合风险预算 Skill

**简体中文** | [English](README.en.md)

> 同一份冻结 CTA 信号，只改组合层资金分配：等权、波动率目标、ERC——风险预算到底改善了扣费后的表现，还是只是把收益削掉了？

<p align="center">
  <img alt="schemes" src="https://img.shields.io/badge/schemes-equal%20%7C%20vol%20%7C%20ERC-blue">
  <img alt="data source" src="https://img.shields.io/badge/data-PandaData-ff69b4">
  <img alt="build" src="https://img.shields.io/badge/BUILD-Q6-7c3aed">
</p>

---

## 这是什么

`risk-budget` 是一个 **BUILD 技能**（Q6）：在 Q2 冻结的商品 CTA 收益矩阵上，只改变组合层权重，比较三套方案：

| 方案 | 权重 | 缩放 |
|---|---|---|
| `equal` 等权 | 每个品种 1/18 | 不缩放，杠杆 1.0 |
| `vol` 波动率目标 | 权重 ∝ 1/过去 60 日波动 | 组合年化波动目标 10%，杠杆上限 1.5，保证金上限 60% |
| `erc` 风险预算 | 60 日协方差等风险贡献优化 | 同样缩放到 10% 波动、杠杆/保证金上限 |

月度再平衡（每月首个交易日，用之前 60 个交易日估计）；换手按双边 1.5bp 计成本。

## 回测结果（2021-01-04 至 2025-12-31）

| 方案 | 累计收益 | 年化 | 年化波动 | Sharpe | 最大回撤 | 年换手 | 平均杠杆 | 保证金占用（均/峰） |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 等权 | **6.25%** | **1.27%** | 11.18% | **0.113** | -22.19% | 0.21x | 1.00 | 20.0% / 20.0% |
| 波动率目标（10%） | 2.54% | 0.52% | 10.84% | 0.048 | **-16.54%** | 2.58x | 1.31 | 26.1% / 30.0% |
| ERC | -0.95% | -0.20% | 10.69% | -0.019 | -19.27% | 5.04x | 1.34 | 26.9% / 30.0% |

**核心结论：风险预算没有改善扣费后的表现。** 等权的收益和风险调整后表现都最好；波动率目标确实降低了回撤（-16.5%），但年化少 0.75 个百分点、换手升到 2.58x；ERC 直接转负。原因是 Q2 收益集中在 JM/AG/AU 等高波动趋势品种，风险缩放把权重从收益来源移走。

## 快速开始

```bash
pip install -r requirements.txt

# 使用随仓库携带的冻结基线
python scripts/build.py --write-production

# 指定基线目录
python scripts/build.py --baseline-dir /path/to/baseline --write-production

# 测试
python scripts/test.py
```

### Python 调用

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

## 输出字段（生产 parquet）

| 字段 | 说明 |
|---|---|
| `trade_date` | 结果所属交易日 |
| `build_id` | `Q6` |
| `build_name` | `risk-budget` |
| `target_id` | 方案（`equal` / `vol` / `erc`） |
| `result_type` | `report` |
| `result_value` | 年化收益 |
| `result_json` | 完整指标与压力月份 |
| `data_version` | 数据版本 |
| `update_time` | 生成时间 |

## 目录结构

```
skill-q6-risk-budget/
├── SKILL.md
├── skill.json
├── scripts/
│   ├── build.py              # BUILD 入口（run / validate_input）
│   ├── engine.py             # 等权 / 波动率目标 / ERC
│   ├── data.py               # 基线读取
│   ├── prepare_baseline.py   # 从 Q2 固化基线
│   └── test.py
├── references/
│   ├── api_guide.md
│   └── baseline/             # CTA 收益 + 保证金率
├── agents/
├── 生产产物/
│   ├── SKILL.md
│   └── 数据库.parquet
└── README.md / README.en.md / INSTALL.md / LICENSE / requirements.txt
```

## 数据来源与口径

- 冻结 CTA 收益：Q2 固定日期换月、18 个商品品种、2021-01-04 至 2025-12-31
- 保证金率：Q2 合约信息按品种取主力合约中位数
- 执行：月度再平衡，按权重变化计双边 1.5bp
- 波动率目标先触发杠杆上限（1.5），保证金峰值约 30%，60% 上限从未绑定
- 不使用随机数或模拟收益

## 局限

- 风险预算的有效性依赖相关性结构；压力期商品高度同向，ERC 的“分散化”会失效
- 结果对协方差窗口、目标波动、杠杆/保证金上限敏感
- 未做容量、冲击成本与品种流动性建模
- 研究用途，不构成投资建议

## ⚠️ 免责声明

- 本项目仅供研究与教育用途，**不构成任何投资建议**，不承诺收益。
- 回测结果基于历史数据与明确假设，未来表现可能显著不同。
- 本项目是 QuantSkills 社区项目，**非 PandaAI 官方背书**，也不代表任何机构认证。
- 使用前请自行核对数据、参数、成本与风险边界。

## 许可证

GNU General Public License v3.0，见 [LICENSE](LICENSE)。
