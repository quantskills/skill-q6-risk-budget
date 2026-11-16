# 安装与接入

## 前置条件

- Python 3.10+
- `pip install -r requirements.txt`

本技能使用随仓库携带的冻结基线，无需 PandaData 凭据即可运行；要换数据时传入自己的 `cta_returns` / `margin`。

## 通用步骤

```bash
git clone https://github.com/quantskills/skill-q6-risk-budget.git
cd skill-q6-risk-budget
pip install -r requirements.txt
python scripts/test.py
python scripts/build.py --write-production
```

## Claude Code

放到 `.claude/skills/risk-budget/`，或直接读取当前目录的 `SKILL.md`。

## Codex

保留仓库根目录的 `SKILL.md`，按 Codex skill 发现规则读取：

```bash
python scripts/build.py --schemes equal vol erc
```

## Cursor

复制到 `.cursor/skills/risk-budget/` 并加载 `agents/cursor-rule.mdc`。

## Hermes / OpenClaw

使用 `agents/portable-loader.md`，把 `<RISK_BUDGET_SKILL_ROOT>` 替换为本地绝对路径。

## 验证

```bash
python scripts/test.py
python -c "import pandas as pd; print(pd.read_parquet('生产产物/数据库.parquet'))"
```

基线可用 `scripts/prepare_baseline.py <q2_project_dir>` 从 Q2 真实数据重新生成。
