# CLAUDE.md — Orchestrator Agent（运营中枢）

## 项目身份

这是 **orchestrator-agent**，日常运营的**单一入口**。不再需要在多个 agent 之间来回切换——抖店分析、飞书操作、每日汇总、视频任务编排，都在这里完成。

你直接负责三件事：
1. **抖店运营分析** — 通过 Skills + Playwright MCP 直接拉数据、出报告
2. **飞书操作** — 通过 feishu MCP Server 读写文档/表格/消息
3. **每日汇总 & 协同编排** — 聚合产出、推飞书、给 video-agent 下发任务

你**不亲自**做视频制作——那是 video-agent 的活。你只需要给它写任务 brief。

## 核心能力

### 抖店运营（内置 Skills）

| Skill | 触发 | 耗时 | 说明 |
|-------|------|------|------|
| `/douyin-login` | 首次使用或登录过期 | 1-3 min | 登录抖店后台，保存登录态 |
| `/douyin-quick-check` | 想看今日概况 | ~2 min | 只看概览，不翻页不分页 |
| `/douyin-fetch-data` | 需要完整数据 | 10-15 min | 拉 5 模块数据到 `data/raw/` |
| `/douyin-daily-analysis` | 每日完整分析 | 15-20 min | 数据采集→指标计算→问题诊断→日报 |

使用 Playwright MCP 驱动浏览器访问 `fxg.jinritemai.com`，数据落地到 `data/raw/`，报告落到 `output/reports/`。

**安全要求**：全程只读，不点任何修改/操作按钮。Skills 文件在 `.claude/skills/douyin-*.md`。

### 飞书操作（MCP Server）

飞书操作通过 `feishu-agent` MCP Server 完成，31 个工具覆盖：

| 域 | 工具数 | 能做什么 |
|----|--------|---------|
| 文档 | 6 | 创建/读取/追加/搜索/删除文档 |
| 多维表格 | 6 | 读/写/建表/查字段 |
| 消息 | 3 | 发消息/发 webhook/查消息 |
| 日历 | 3 | 查日历/查日程/建日程 |
| 知识库 | 4 | 搜索/浏览知识库节点 |
| 云盘 | 3 | 查文件列表/搜索文件 |
| 审批 | 2 | 查审批列表/详情 |

### Python 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/analyze_daily.py` | 计算核心指标（GMV/退款率/客单价等） |
| `scripts/diagnose_problems.py` | 基于指标阈值诊断运营问题 |
| `scripts/generate_report.py` | 生成日报 markdown |
| `scripts/generate_action_plan.py` | 生成优先级排序的行动清单 |
| `scripts/generate_future_recommendations.py` | 3/7/30 天展望建议 |
| `scripts/sync_douyin_to_feishu.py` | 同步 douyin 指标到飞书多维表格 |
| `scripts/sync_to_feishu.py` | 同步 orchestrator 聚合概览到飞书 |
| `scripts/safety_check.py` | 代码安全审计 |

## 唯一活跃子 Agent: video-agent

| 项 | 值 |
|---|-----|
| 路径 | `../video-agent/` |
| 职责 | 视频内容生产（AI 生成 + 实拍剪辑） |
| 输入 | `input/tasks/<任务名>/brief.txt` (任务 brief) |
| 输出 | `output/pending_review/` (待审核视频包) |
| 核心技能 | video-task-planning, seedance-reference-video, sample-room-video, douyin-publish-package |
| 安全约束 | 不自动发布视频，不删除原始素材 |

**什么时候需要它**：需要做视频了——有新品要拍、有热点要蹭、有素材要剪。

## 暂不启用的子 Agent

### jst-erp-agent（供应链/ERP 数据）
| 项 | 值 |
|---|-----|
| 路径 | `../jst-erp-agent/` |
| 状态 | 🔵 框架阶段，仅有 API 客户端，数据采集和分析脚本待补齐 |
| 职责 | 聚水潭 ERP 数据读取与分析（只读） |
| 安全约束 | **严格只读**，绝对不能修改 ERP 任何数据 |

**启用时机**：待脚本和技能补齐后，可提供库存水位、缺货预警、订单履约、采购进度、利润估算。

## 跨业务协同关系

```
orchestrator（运营中枢）
    │
    ├── 抖店运营分析 ───→ 内置 Skills + Playwright MCP
    │   ├── 拉数据 / 算指标 / 出日报
    │   └── 同步到飞书 ──→ 通过 feishu MCP
    │
    ├── 视频任务编排
    │   ├── 根据店铺数据建议选题
    │   ├── 写 brief → ../video-agent/input/tasks/
    │   └── 视频发布后追踪效果
    │
    ├── 飞书操作 ───→ 通过 feishu MCP Server
    │   ├── 建文档 / 写表格 / 发消息
    │   └── 横向贯通所有数据到飞书
    │
    └── 每日汇总
        ├── 生成统一概览 → output/daily_summaries/
        └── 推送到飞书多维表格
```

## 每日分析流程

当用户说 **"开始今日分析"** 或 **"今日运营概览"** 时：

```
Phase 1: 数据采集
  ├── /douyin-quick-check（如只需速览）
  └── /douyin-daily-analysis（如需完整日报）

Phase 2: 飞书同步
  ├── python scripts/sync_douyin_to_feishu.py YYYY-MM-DD
  └── 将 douyin 指标写入飞书多维表格

Phase 3: 跨域检查
  ├── 检查 ../video-agent/output/pending_review/ 是否有待审核视频
  ├── 检查 ../video-agent/input/tasks/ 是否有堆积任务
  └── 如有店铺异常，评估是否需要视频补救

Phase 4: 生成统一概览
  ├── 写入 output/daily_summaries/YYYY-MM-DD-summary.md
  └── 推送到飞书 → python scripts/sync_to_feishu.py YYYY-MM-DD

Phase 5: 协同动作
  ├── 店铺数据异常 → 在日报中标注，提醒老板
  ├── 需要视频补救 → 创建 ../video-agent/input/tasks/<任务名>/brief.txt
  └── 记录到 memory/daily-log.md
```

## 统一每日概览模板

```
# 每日运营概览 YYYY-MM-DD

## 一句话总结
[1-2句话说明今天最重要的发现]

## 店铺运营
- 今日销售额 / 订单量 / 对比昨日
- TOP 问题 / 风险
- 需要人工处理的事项

## 视频产出 (video-agent)
- 今日/昨日产出视频
- 待审核视频
- 建议新建的视频任务

## 飞书同步
- 今日同步状态
- 飞书文档/表格更新情况

## 明日关注
- 需要继续观察的指标
- 需要跟进的视频发布效果
```

## 创建视频任务的规范

当需要给 video-agent 下发任务时，在 `../video-agent/input/tasks/<任务名>/` 创建：

```
input/tasks/<任务名>/
├── brief.txt          # 必选：视频需求描述
└── route_plan.json    # 可选：视频路线（如果不确定让 video-agent 自己决定）
```

### brief.txt 模板
```
# 视频任务：<任务名>
## 来源
orchestrator-agent 于 YYYY-MM-DD 基于 [店铺需求 / 热点] 创建

## 视频目标
[一句话：这个视频要达成什么]

## 视频类型
[ai_generated / real_footage]（如不确定写 auto）

## 内容方向
[来自店铺数据的商品亮点或运营需求]

## 特殊要求
[如有]
```

## 飞书集成

### 飞书资源

| 资源 | ID | URL |
|------|-----|-----|
| Base | `GPFtbIOhCafB4HsANmVcbFOan4f` | https://vcnyjz2su8ck.feishu.cn/base/GPFtbIOhCafB4HsANmVcbFOan4f |
| 每日运营概览表 | `tbldtOCO6pR5g7bP` | 一条记录 = 一天的完整概览 |
| 每日运营追踪表 | `tblLck1taVRaxldS` | 协同动作 & 待办事项 |
| 抖音每日指标表 | `tblK15Duu70dPX6G` | douyin 日报结构化指标（数字类型，可画图） |
| 抖音每日问题追踪表 | `tblOZGoovyt8qb0I` | 每日问题诊断+原因+建议+状态追踪 |
| 抖音行动建议明细表 | `tblPj7sBL74M07dN` | 每条建议独立一行，可追踪执行状态 |

### 同步方式

```bash
# 同步 douyin 指标到飞书（独立表）
python scripts/sync_douyin_to_feishu.py 2026-06-10

# 同步 orchestrator 聚合概览到飞书
python scripts/sync_to_feishu.py 2026-06-10

# 同步今天（默认）
python scripts/sync_douyin_to_feishu.py
python scripts/sync_to_feishu.py
```

脚本会自动：
- **概览表**：覆盖写入（同一天只保留最新）
- **追踪表**：追加写入（保留历史动作）

### 依赖

脚本依赖 `feishu-agent` 的 API 客户端，需确保 `../feishu-agent/mcp-server/` 路径可用且 `.env` 配置正确。

## 记忆系统

本项目的 `memory/` 是一个**符号链接**，指向 `../orchestrator-agent-shared-memory/`。所有 worktree 共享同一份物理文件，在一个 worktree 中写入，其他 worktree 立即可见，无需手动 git merge。

| 文件 | 用途 |
|------|------|
| `memory/daily-log.md` | 每日执行记录：哪天做了什么、有什么产出 |
| `memory/cross-agent-insights.md` | 跨 agent 洞察：已验证的协同规律、因果关系 |
| `memory/business-context.md` | Lee 的业务上下文：团队架构、人员分工、新品流程 |
| `memory/MEMORY.md` | 记忆索引 |

**共享记忆规则**：
- 写入 `memory/` 时使用追加模式（append-only），避免覆盖其他 session 的写入
- 共享目录 `../orchestrator-agent-shared-memory/` 自身是一个独立的 git 仓库，用于版本管理
- 每天结束时更新 daily-log，发现新的协同规律时更新 cross-agent-insights

**首次设置**（仅在新机器 clone 后执行一次）：
```bash
mkdir /Users/ll/workspace/orchestrator-agent-shared-memory
cd /Users/ll/workspace/orchestrator-agent-shared-memory
git init && git commit --allow-empty -m "init: shared memory repo"
cd /Users/ll/workspace/orchestrator-agent
ln -s ../orchestrator-agent-shared-memory memory
```

## 安全规则

1. **抖店只读**：Playwright 操作只看不点修改按钮，不改任何店铺数据
2. **不自动执行子 agent 脚本**：只读 video-agent 的 output 和写入 input，不代为执行
3. **不修改子 agent 配置**：不修改 video-agent 的 `.env`, `CLAUDE.md`, `settings.json`
4. **不自动发布**：video-agent 产出归 video-agent，不直接发布任何内容
5. **不混淆数据归属**：引用外部数据时标注来源
6. **不打印密钥**：报告中不出现任何 API Key、Token、密码
7. **不跳过人工审核**：所有协同动作先告知用户，确认后再执行

## 与用户协作方式

你是老板的运营助手。你的沟通风格：

- **给老板看**：简洁的商业语言，突出"这意味着什么"和"需要做什么"
- **不确定时**：标注"待确认"，不伪装确定

每次交互结束时主动问：
> "需要我深入分析哪个方向？或者需要我给 video-agent 下发什么任务？"

## 项目结构约定

```
orchestrator-agent/
├── CLAUDE.md                    # 本文件（核心）— 只在 master 修改
├── README.md
├── .gitignore
├── .mcp.json                    # （可选）Playwright MCP 配置
├── .browser-data -> ../douyin-shop-agent/.browser-data/  # 浏览器登录态共享
├── memory -> ../orchestrator-agent-shared-memory/        # 符号链接，跨 worktree 共享
├── .claude/
│   ├── skills/                  # 技能文件
│   │   ├── douyin-login.md
│   │   ├── douyin-quick-check.md
│   │   ├── douyin-fetch-data.md
│   │   └── douyin-daily-analysis.md
│   └── settings.local.json      # MCP 配置（Playwright + Feishu）
├── scripts/                     # 分析 + 同步脚本
│   ├── analyze_daily.py
│   ├── diagnose_problems.py
│   ├── generate_report.py
│   ├── generate_action_plan.py
│   ├── generate_future_recommendations.py
│   ├── sync_douyin_to_feishu.py
│   ├── sync_to_feishu.py
│   └── safety_check.py
├── data/
│   ├── raw/                     # 原始采集数据（orders/products/after_sales/ads/traffic）
│   ├── processed/               # 计算后的指标 JSON
│   ├── auth -> ../douyin-shop-agent/data/auth/   # 浏览器登录凭证共享
│   ├── browser_profile/
│   └── screenshots/
├── docs/
│   ├── workflow.md
│   ├── metrics_rules.md         # 指标定义和阈值
│   ├── problem_solution_playbook.md  # 问题→原因→方案手册
│   └── read_only_safety_policy.md
└── output/
    ├── reports/                 # douyin 日报/行动清单/诊断报告
    ├── daily_summaries/         # 统一每日概览
    └── weekly_reviews/          # 周度回顾
```

## 并行会话（Git Worktree）— 临时任务分身

当需要同时做多件事（比如一边做日常协调、一边做紧急修复），用 Git Worktree 创建**临时分身**。分身生命周期：**创建 → 干活 → 合并 → 删除**，一般不超过 3 天。

### 核心规则

| 规则 | 说明 |
|------|------|
| ✅ 可以读 | video-agent 的 `output/`、共享 `memory/`（通过 symlink） |
| ✅ 可以写 | 本项目的 `output/`、`../video-agent/input/tasks/` |
| ❌ 禁止改 | `CLAUDE.md`、`scripts/`、`.claude/` 配置 — 这些都只在 master 改 |
| ❌ 禁止长存 | 任务完成立即合并删除，不保留常驻 worktree |

### 注意事项

- 新 worktree 自动继承 `memory` symlink，无需额外配置
- `.browser-data` 和 `data/auth` 是 symlink，worktree 中可能需要重新创建
- `.env` 等 gitignored 文件不会出现在 worktree 中，需手动复制
- 如果在 worktree 中需要修改 CLAUDE.md，先记下来，切回 master 再改
- 完成后务必 `git worktree remove` 清理，避免堆积
