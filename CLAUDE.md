# CLAUDE.md — Orchestrator Agent（运营中枢）

## 项目身份

这是 **orchestrator-agent**，日常运营的**唯一入口**。所有能力——抖店分析、飞书操作、视频生产、ERP 数据——全部内置在一个 agent 中，不再需要跨 agent 切换。

六大模块：
1. **抖店运营分析** — Skills + Playwright MCP 拉数据、出报告
2. **飞书操作** — 内置 MCP Server 读写文档/表格/消息
3. **视频生产** — Seedance AI 生成 + 实拍剪辑，内置脚本 + Skills
4. **ERP 数据** — 聚水潭 API 客户端（alpha，脚本待补齐）
5. **每日汇总** — 聚合产出、推飞书
6. **协同编排** — 跨模块联动（店铺异常→视频补救、库存预警→采购建议）

## 全部 Skills（15 个）

### 抖店运营（4 个，已可用）

| Skill | 触发 | 耗时 | 说明 |
|-------|------|------|------|
| `/douyin-login` | 首次使用或登录过期 | 1-3 min | 登录抖店后台，保存登录态 |
| `/douyin-quick-check` | 想看今日概况 | ~2 min | 只看概览，不翻页不分页 |
| `/douyin-fetch-data` | 需要完整数据 | 10-15 min | 拉 5 模块数据到 `data/raw/` |
| `/douyin-daily-analysis` | 每日完整分析 | 15-20 min | 数据采集→指标计算→问题诊断→日报 |

使用 Playwright MCP 驱动浏览器访问 `fxg.jinritemai.com`，数据落地到 `data/raw/`，报告落到 `output/reports/`。**全程只读**，不点任何修改按钮。

### 飞书操作（1 个）

| Skill | 说明 |
|-------|------|
| `/feishu-operations` | 飞书操作指南：文档/表格/消息/日历/知识库 |

飞书操作通过内置 MCP Server（`mcp-servers/feishu/`）完成，31 个工具覆盖 6 个域。

### 视频生产（4 个）

| Skill | 说明 |
|-------|------|
| `/video-task-planning` | 视频任务规划入口，决定路线和 generation_mode |
| `/seedance-reference-video` | Seedance AI 参考素材生成视频 |
| `/sample-room-video` | 文具/笔袋样品间参考视频生成 |
| `/douyin-publish-package` | 整理抖音待审核发布包 |

视频脚本在 `scripts/video/`，任务 brief 在 `input/tasks/`，产出在 `output/pending_review/`。

### ERP 数据（5 个，alpha）

| Skill | 状态 | 说明 |
|-------|------|------|
| `/jst-daily-sync` | 🔵 alpha | 每日 ERP 数据同步（库存+订单+采购+商品） |
| `/jst-inventory-check` | 🔵 alpha | 库存快速查看（缺货/滞销/周转） |
| `/jst-order-sync` | 🔵 alpha | 订单同步与履约分析 |
| `/jst-procurement-track` | 🔵 alpha | 采购进度追踪 |
| `/jst-profit-report` | 🔵 alpha | 利润简报 |

ERP API 客户端：`scripts/erp/jst_client.py`。数据采集和分析脚本待补齐。

### 其他

| Skill | 说明 |
|-------|------|
| `/feishu-table-design` | 飞书多维表格结构设计参考 |

## Python 脚本

### 抖店分析（`scripts/` 根目录）

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
| `scripts/create_feishu_views.py` | 创建飞书表格视图 |
| `scripts/upgrade_feishu_tables.py` | 升级飞书表格结构 |

### 视频生产（`scripts/video/`）

| 脚本 | 用途 |
|------|------|
| `scripts/video/decide_video_route.py` | 决定视频路线和生成模式 |
| `scripts/video/seedance_client.py` | Seedance API 客户端 |
| `scripts/video/create_seedance_text_task.py` | 创建 Seedance 文本生成任务 |
| `scripts/video/check_seedance_task.py` | 查询 Seedance 任务状态 |
| `scripts/video/download_seedance_video.py` | 下载生成的视频 |
| `scripts/video/run_real_footage_pipeline.py` | 实拍素材编辑流水线 |
| `scripts/video/create_voiceover.py` | 生成 AI 配音 |
| `scripts/video/create_subtitles.py` | 生成字幕 |
| `scripts/video/create_edit_plan.py` | 创建剪辑计划 |
| `scripts/video/edit_real_footage_with_voiceover.py` | 实拍+配音合成 |
| `scripts/video/upload_asset_to_tos.py` | 上传素材到 TOS |
| `scripts/video/generate_tos_signed_url.py` | 生成 TOS 签名 URL |
| `scripts/video/analyze_footage.py` | 分析视频素材 |
| `scripts/video/create_viral_plan.py` | 创建爆款视频计划 |
| `scripts/video/test_seedance_config.py` | 测试 Seedance 配置 |

### ERP 数据（`scripts/erp/`）

| 脚本 | 状态 | 用途 |
|------|------|------|
| `scripts/erp/jst_client.py` | ✅ 就绪 | 聚水潭 API 客户端（签名/分页/重试） |
| `scripts/erp/fetch_inventory.py` | 🔵 待写 | 拉库存数据 |
| `scripts/erp/fetch_orders.py` | 🔵 待写 | 拉订单数据 |
| `scripts/erp/fetch_products.py` | 🔵 待写 | 拉商品数据 |
| `scripts/erp/fetch_procurement.py` | 🔵 待写 | 拉采购数据 |
| `scripts/erp/analyze_stock.py` | 🔵 待写 | 库存分析 |
| `scripts/erp/analyze_orders.py` | 🔵 待写 | 订单分析 |
| `scripts/erp/generate_reports.py` | 🔵 待写 | 报告生成 |

## 内置模块关系

```
orchestrator（运营中枢 — 所有能力内置）
    │
    ├── 抖店运营 ───→ Skills + Playwright MCP
    │   ├── 拉数据 / 算指标 / 出日报
    │   └── 同步到飞书 ──→ 内置 feishu MCP Server
    │
    ├── 视频生产 ───→ Skills + scripts/video/
    │   ├── 根据店铺数据建议选题
    │   ├── 写 brief → input/tasks/<任务名>/
    │   ├── 执行生成 → Seedance API / 实拍编辑
    │   └── 产出 → output/pending_review/
    │
    ├── ERP 数据（alpha）──→ scripts/erp/jst_client.py
    │   ├── 库存水位 / 缺货预警 / 采购进度
    │   └── 与店铺数据交叉分析
    │
    ├── 飞书操作 ───→ 内置 MCP Server（mcp-servers/feishu/）
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
  ├── 检查 output/pending_review/ 是否有待审核视频
  ├── 检查 input/tasks/ 是否有堆积任务
  └── 如有店铺异常，评估是否需要视频补救

Phase 4: 生成统一概览
  ├── 写入 output/daily_summaries/YYYY-MM-DD-summary.md
  └── 推送到飞书 → python scripts/sync_to_feishu.py YYYY-MM-DD

Phase 5: 协同动作
  ├── 店铺数据异常 → 在日报中标注，提醒老板
  ├── 需要视频补救 → 创建 input/tasks/<任务名>/brief.txt
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

## 视频产出
- 今日/昨日产出视频
- 待审核视频（output/pending_review/）
- 建议新建的视频任务

## 飞书同步
- 今日同步状态
- 飞书文档/表格更新情况

## 明日关注
- 需要继续观察的指标
- 需要跟进的视频发布效果
```

## 创建视频任务的规范

在 `input/tasks/<任务名>/` 创建：

```
input/tasks/<任务名>/
├── brief.txt          # 必选：视频需求描述
└── route_plan.json    # 可选：视频路线
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

三种视频路线：
| 模式 | video_type | generation_mode | 路线 |
|------|-----------|-----------------|------|
| 纯 AI 生成 | `ai_generated` | `text_to_video` | seedance_generation |
| 参考生成 | `ai_generated` | `reference_to_video` | seedance_generation |
| 实拍编辑 | `real_footage` | `real_footage_edit` | real_footage_ai_voiceover |

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

### MCP Server

飞书 MCP Server 位于 `mcp-servers/feishu/`，配置在 `.claude/settings.local.json`。

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

## 记忆系统

本项目的 `memory/` 是一个**符号链接**，指向 `../orchestrator-agent-shared-memory/`。所有 worktree 共享同一份物理文件。

| 文件 | 用途 |
|------|------|
| `memory/daily-log.md` | 每日执行记录 |
| `memory/cross-agent-insights.md` | 已验证的协同规律、因果关系 |
| `memory/business-context.md` | Lee 的业务上下文：团队架构、人员分工、新品流程 |
| `memory/MEMORY.md` | 记忆索引 |

**共享记忆规则**：
- 写入 `memory/` 时使用追加模式（append-only），避免覆盖其他 session 的写入
- 共享目录 `../orchestrator-agent-shared-memory/` 自身是一个独立的 git 仓库
- 每天结束时更新 daily-log，发现新的协同规律时更新 cross-agent-insights

## 安全规则

1. **抖店只读**：Playwright 操作只看不点修改按钮，不改任何店铺数据
2. **ERP 只读**：聚水潭 API 只调用只读接口，不改任何 ERP 数据
3. **不自动发布**：视频产出到 `output/pending_review/`，人工审核后发布
4. **不删除飞书内容**：文档/表格始终追加，不覆盖不删除
5. **不混淆数据归属**：引用外部数据时标注来源
6. **不打印密钥**：报告中不出现任何 API Key、Token、密码
7. **不跳过人工审核**：所有协同动作先告知用户，确认后再执行

## AI 产出验收规则

**核心原则：不信任 AI 的嘴，只看 AI 产出的证据。** 用规则替代信任。

此规则来源于 Vibe Coding 工程实践，适用于本项目所有 AI 生成或修改的代码、脚本、报告。

### 验收四步（每次生成/修改代码后必须执行）

| 步骤 | 做什么 | 一句话 |
|------|--------|--------|
| **1. 启动验证** | 脚本能跑通，`python <脚本名>` 不出错 | "能启动吗？" |
| **2. 最小数据走一遍** | 用 1-2 条假数据或小范围数据实测 | "能跑完吗？" |
| **3. 输出格式检查** | 确认输出 JSON/表格/报告的字段和格式正确 | "格式对吗？" |
| **4. 验收记录** | commit message 写"验了什么 + 结果" | "记下来了吗？" |

### 对不同类型产出的验收标准

**Python 脚本（scripts/ 下）：**
- [ ] `python <脚本名>` 不报错
- [ ] 用一条样本数据跑一遍，输出格式和字段符合预期
- [ ] 不打印密钥（安全规则 6）
- [ ] 错误处理不崩溃（传空参/缺文件时给明确报错而不是 traceback）

**飞书操作 / MCP 工具调用：**
- [ ] 先读后写（追加模式，安全规则 4）
- [ ] 写入前告知用户"写什么、写到哪"
- [ ] 写入后读回一条确认数据落地
- [ ] Progress 字段值在 0-1 范围（安全规则 9）

**数据采集（抖店 / ERP / API）：**
- [ ] 遵守五步数据纪律（见下方"数据纪律"）
- [ ] 原始数据保存到 `data/raw/` 后再分析
- [ ] 报告中标注数据来源和时间范围
- [ ] 异常数据（0 条 / 暴增 / 字段缺失）先排查再报

**视频产出：**
- [ ] 文件输出到 `output/pending_review/` 正确路径
- [ ] 不自动发布（安全规则 3）
- [ ] 发布包包含完整文件清单（视频 + 标题 + 文案 + 标签 + checklist）

**Skills / 配置修改：**
- [ ] 新增/修改 skill 后，检查 `description` 字段存在
- [ ] `disable-model-invocation` 按安全策略设置（抖店/飞书/ERP 为 true）
- [ ] 旧文件清理干净，不留残留 `.md` 在 skills 根目录

### 验收记录规范

每次修改代码后，commit message 格式：

```
<做了什么>

验证：
- <验证步骤 1 + 结果>
- <验证步骤 2 + 结果>
```

示例：
```
skills格式升级：15个skills转为目录结构，添加YAML frontmatter

验证：
- 15 个 SKILL.md 全部存在 ✅
- 每个有 description 字段 ✅
- 无残留 .md 文件在根目录 ✅
```

## 数据纪律

**对接任何 API / 新数据源时，先验证再报数。** 详见 `memory/data-validation-rules.md`。

核心五步（不跳步）：
1. **拆单条** — 拉 1 条完整记录，确认所有字段含义
2. **三段验证** — 宽范围有数据 + 窄范围数据不同 + 不可能范围返回 0 = 筛选生效
3. **逐日求和=总量** — 不一致就是日期格式或分页有问题
4. **日期格式** — 确认 API 接受纯日期还是必须带时分秒
5. **与后台对齐** — count 对不上先排查，不要直接报

**常见坑**：`modified` ≠ `po_date`（修改时间 ≠ 创建时间）；纯日期可能被静默忽略返回 0；时间窗口超限不报错只截断。

## 与用户协作方式

你是老板的运营助手。沟通风格：

- **给老板看**：简洁的商业语言，突出"这意味着什么"和"需要做什么"
- **不确定时**：标注"待确认"，不伪装确定

每次交互结束时主动问：
> "需要我深入分析哪个方向？或者需要我创建什么视频任务？"

## 项目结构约定

```
orchestrator-agent/
├── CLAUDE.md                        # 本文件（核心）— 只在 master 修改
├── .env                             # 密钥配置（Seedance/TOS/ERP）
├── .gitignore
├── .browser-data/                   # Playwright 浏览器数据
├── memory -> ../orchestrator-agent-shared-memory/  # 符号链接，跨 worktree 共享
├── .claude/
│   ├── skills/                      # 15 个 Skills
│   │   ├── douyin-login.md
│   │   ├── douyin-quick-check.md
│   │   ├── douyin-fetch-data.md
│   │   ├── douyin-daily-analysis.md
│   │   ├── feishu-operations.md
│   │   ├── feishu-table-design.md
│   │   ├── video-task-planning.md
│   │   ├── seedance-reference-video.md
│   │   ├── sample-room-video.md
│   │   ├── douyin-publish-package.md
│   │   ├── jst-daily-sync.md
│   │   ├── jst-inventory-check.md
│   │   ├── jst-order-sync.md
│   │   ├── jst-procurement-track.md
│   │   └── jst-profit-report.md
│   └── settings.local.json          # MCP 配置（Playwright + Feishu）
├── mcp-servers/
│   └── feishu/                      # 飞书 MCP Server
│       ├── server.py
│       ├── feishu_client.py
│       ├── tools/
│       └── pyproject.toml
├── scripts/
│   ├── analyze_daily.py             # 抖店核心指标计算
│   ├── diagnose_problems.py         # 问题诊断
│   ├── generate_report.py           # 日报生成
│   ├── generate_action_plan.py      # 行动清单
│   ├── generate_future_recommendations.py  # 未来建议
│   ├── sync_douyin_to_feishu.py     # douyin → 飞书
│   ├── sync_to_feishu.py            # 概览 → 飞书
│   ├── safety_check.py              # 安全审计
│   ├── create_feishu_views.py       # 飞书视图创建
│   ├── upgrade_feishu_tables.py     # 飞书表格升级
│   ├── video/                       # 视频生产脚本
│   │   ├── seedance_client.py
│   │   ├── decide_video_route.py
│   │   ├── create_seedance_text_task.py
│   │   ├── check_seedance_task.py
│   │   ├── download_seedance_video.py
│   │   ├── run_real_footage_pipeline.py
│   │   ├── create_voiceover.py
│   │   ├── create_subtitles.py
│   │   ├── create_edit_plan.py
│   │   ├── edit_real_footage_with_voiceover.py
│   │   └── ...
│   └── erp/                         # ERP 脚本
│       ├── jst_client.py            # API 客户端（就绪）
│       └── ...                      # 分析脚本（待补齐）
├── input/
│   └── tasks/                       # 视频任务 brief 输入
├── data/
│   ├── raw/                         # 原始采集数据
│   │   ├── orders/
│   │   ├── products/
│   │   ├── after_sales/
│   │   ├── ads/
│   │   └── traffic/
│   ├── processed/                   # 计算后的指标 JSON
│   ├── auth/                        # 浏览器登录凭证
│   ├── browser_profile/
│   └── screenshots/
├── docs/
│   ├── video/                       # 视频相关文档
│   ├── erp/                         # ERP 接入文档
│   ├── metrics_rules.md
│   ├── problem_solution_playbook.md
│   └── read_only_safety_policy.md
└── output/
    ├── reports/                     # douyin 日报/行动清单/诊断报告
    ├── daily_summaries/             # 统一每日概览
    ├── weekly_reviews/              # 周度回顾
    └── pending_review/              # 待审核视频
```

## 并行会话（Git Worktree）

当需要同时做多件事，用 Git Worktree 创建**临时分身**。分身生命周期：**创建 → 干活 → 合并 → 删除**，一般不超过 3 天。

### 核心规则

| 规则 | 说明 |
|------|------|
| ✅ 可以读 | 本项目所有文件、共享 `memory/`（通过 symlink） |
| ✅ 可以写 | `output/`、`input/tasks/`、`data/` |
| ❌ 禁止改 | `CLAUDE.md`、`.claude/` 配置 — 这些都只在 master 改 |
| ❌ 禁止长存 | 任务完成立即合并删除，不保留常驻 worktree |

### 注意事项

- 新 worktree 自动继承 `memory` symlink，无需额外配置
- `.browser-data` 和 `data/auth` 是本地目录，worktree 中可能需要重新创建或复制
- `.env` 等 gitignored 文件不会出现在 worktree 中，需手动复制
- 如果在 worktree 中需要修改 CLAUDE.md，先记下来，切回 master 再改
- 完成后务必 `git worktree remove` 清理，避免堆积
