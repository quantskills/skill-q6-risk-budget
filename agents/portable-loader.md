# Portable Loader Prompt

Use this prompt in agents that do not natively discover `SKILL.md` folders, including Claude Code, Hermes, and OpenClaw deployments that receive skills as copied folders.

```text
You have access to a local skill named risk-budget at:
<RISK_BUDGET_SKILL_ROOT>

When the user asks whether risk budgeting improves after-cost CTA performance, wants to audit leverage and margin usage, compare ERC with equal weight, or reproduce the Q6 study:
1. Read <RISK_BUDGET_SKILL_ROOT>/SKILL.md.
2. For input schemas and baseline files, read <RISK_BUDGET_SKILL_ROOT>/references/api_guide.md.
3. Run python scripts/build.py --write-production before reading production results.
4. Preserve schemes, vol target, leverage/margin caps, covariance window, costs, and data dates.
5. Do not invent data fields, weights, returns, or allocation advice.
```
