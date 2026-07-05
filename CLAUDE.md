# CLAUDE.md — Orchestrator Agent（历史目录树快照）

> 本文件是 Claude Code → Codex 迁移来源的历史快照，仅保留目录结构供参考。
> **所有业务规则、开发规范、任务指引、Skills 清单均已迁移至 [AGENTS.md](AGENTS.md)。**
> **模板、验收规则、数据纪律、飞书集成等细节见 [docs/catalog.md](docs/catalog.md)。**

## 项目身份

**orchestrator-agent** — 日常运营统一中枢（抖店 / 视频 / ERP / 飞书 / 协同编排）。
最后一次从 Claude Code 迁移：2026-07-03。

## 项目目录树

```
orchestrator-agent/
├── AGENTS.md                       # 唯一规则入口
├── CLAUDE.md                       # 本文件（历史目录树快照）
├── .env                            # 密钥配置
├── .gitignore
├── .browser-data/                  # Playwright 浏览器数据
├── memory -> ../orchestrator-agent-shared-memory/  # 符号链接，跨 worktree 共享
├── .claude/
│   ├── skills/                     # Skills（子目录格式 SKILL.md）
│   │   ├── douyin-login/SKILL.md
│   │   ├── douyin-quick-check/SKILL.md
│   │   ├── douyin-fetch-data/SKILL.md
│   │   ├── douyin-daily-analysis/SKILL.md
│   │   ├── video-task-planning/SKILL.md
│   │   ├── seedance-reference-video/SKILL.md
│   │   ├── sample-room-video/SKILL.md
│   │   ├── douyin-publish-package/SKILL.md
│   │   ├── jst-daily-sync/SKILL.md
│   │   ├── jst-inventory-check/SKILL.md
│   │   ├── jst-order-sync/SKILL.md
│   │   ├── jst-procurement-track/SKILL.md
│   │   ├── jst-profit-report/SKILL.md
│   │   ├── market-insight/SKILL.md
│   │   ├── competitor-analysis/SKILL.md
│   │   ├── idea-validator/SKILL.md
│   │   ├── planning-with-files/SKILL.md
│   │   ├── skill-creator/SKILL.md
│   │   └── agent-browser -> ../../.agents/skills/agent-browser
│   └── settings.local.json         # MCP 配置
├── .codex/                         # Codex 侧配置
├── scripts/
│   ├── analyze_daily.py
│   ├── diagnose_problems.py
│   ├── generate_report.py
│   ├── generate_action_plan.py
│   ├── generate_future_recommendations.py
│   ├── safety_check.py
│   ├── video/                      # 视频生产脚本
│   └── erp/                        # ERP 脚本
├── input/
│   └── tasks/                      # 视频任务 brief
├── data/
│   ├── raw/                        # 原始采集数据
│   ├── processed/                  # 计算后的指标 JSON
│   ├── auth/                       # 浏览器登录凭证
│   └── screenshots/
├── docs/
│   ├── catalog.md                  # 完整参考手册
│   ├── video/                      # 视频相关文档
│   └── erp/                        # ERP 接入文档
└── output/
    ├── reports/                    # 日报/行动清单
    ├── daily_summaries/            # 统一每日概览
    └── pending_review/             # 待审核视频
```
