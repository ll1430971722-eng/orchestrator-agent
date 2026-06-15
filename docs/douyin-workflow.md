# 抖店运营完整工作流

> 从登录到飞书同步的端到端全景图。
> 最后更新：2026-06-15

---

## 流程全景图

```
┌──────────────────────────────────────────────────────────────────────┐
│                    抖店运营每日分析 — 端到端流程                        │
│                                                                      │
│  ┌─────────┐   ┌──────────────┐   ┌──────────────┐   ┌────────────┐ │
│  │ 1. 登录  │──▶│ 2. 数据采集   │──▶│ 3. 分析 & 诊断 │──▶│ 4. 报告生成 │ │
│  │ (Login)  │   │ (Fetch Data) │   │ (Analyze)    │   │ (Report)   │ │
│  └─────────┘   └──────────────┘   └──────────────┘   └────────────┘ │
│                      │                   │                  │        │
│                      ▼                   ▼                  ▼        │
│               data/raw/           LLM 上下文内         output/reports/ │
│               *.md 文件           实时计算+推理         *.md 文件       │
│                                                                      │
│                                          ┌────────────┐              │
│                                          │ 5. 飞书同步  │              │
│                                          │ (Sync)      │              │
│                                          └────────────┘              │
│                                                │                     │
│                                                ▼                     │
│                                    飞书多维表格 3 张表                  │
│                                    (指标表+问题表+行动表)               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 环节 1：登录 (`douyin-login`)

| 项目 | 内容 |
|------|------|
| **触发** | 首次使用，或登录态过期 |
| **耗时** | 1-3 分钟 |
| **工具** | Playwright MCP (`browser_navigate`, `browser_type`, `browser_click`, `browser_snapshot`) |
| **输入** | `.env` 中的 `DOUYIN_LOGIN_ACCOUNT` / `DOUYIN_LOGIN_PASSWORD`（可选） |
| **输出** | 浏览器登录态由 Playwright persistent context 自动保存 |
| **状态** | ✅ 已可用 |

### 执行流程

```
browser_navigate → fxg.jinritemai.com/login/common
    │
    ├─ 已有登录态 → 直接进入后台 → ✅ 完成
    │
    └─ 在登录页 → browser_type 输入账号密码
                    │
                    ├─ 无验证码 → browser_click 登录 → ✅ 完成
                    │
                    └─ 有验证码 → 提示用户手动完成 → 轮询检测 → ✅ 完成
```

### 关键细节

- 登录态保存在 `.browser-data/`（Playwright persistent context）
- 凭证从 `.env` 读取，不写死在 Skill 或代码中
- 验证码需要人工介入，skill 会提示用户并轮询等待

---

## 环节 2：数据采集

### 2a. 快速检查 (`douyin-quick-check`)

| 项目 | 内容 |
|------|------|
| **触发** | 只想快速扫一眼今日概况 |
| **耗时** | ~2 分钟 |
| **输出** | 纯文本，不生成文件 |
| **状态** | ✅ 已可用 |

只看首页仪表盘核心指标卡 + 数据罗盘概览，不翻页不提取完整表格。

### 2b. 完整采集 (`douyin-fetch-data`)

| 项目 | 内容 |
|------|------|
| **触发** | 需要完整数据用于分析 |
| **耗时** | 10-15 分钟 |
| **工具** | Playwright MCP (`browser_navigate`, `browser_snapshot`, `browser_evaluate`, `browser_screenshot`) |
| **输出** | `data/raw/YYYY-MM-DD/` 下的 Markdown 文件 |
| **状态** | ✅ 已可用 |

#### 采集的 5 个模块

```
模块              抖店 URL                                    提取方法              输出文件
─────────────────────────────────────────────────────────────────────────────────────────
仪表盘概览         fxg.jinritemai.com/                        browser_snapshot       dashboard-overview.md
                                                                                     (包含：体验分、实时指标、
                                                                                      7日趋势、搜索/短视频/
                                                                                      联盟/618/诊断/待办)

订单管理           fxg.jinritemai.com/order/list              browser_snapshot       orders-summary.md
                                                                                     (包含：订单总览、今日订单
                                                                                      表格、昨日订单摘要)

商品管理           fxg.jinritemai.com/product/list            browser_snapshot       products-summary.md
                                                                                     (包含：商品列表、爆品分析)

售后管理           fxg.jinritemai.com/after-sale/refund/list  browser_snapshot       aftersales-summary.md
                                                                                     (包含：售后列表、退款原因)

广告/推广          fxg.jinritemai.com/promotion/manage        browser_snapshot       ads-summary.md
                                                                                     (如未开通则记录"无广告数据")
```

#### 实际数据格式（以 2026-06-15 为例）

Skill 文档中定义了理想格式（用 `browser_evaluate` 提取 JSON），但实际执行中使用 `browser_snapshot` 获取页面文本快照，保存为 Markdown。这是务实的选择——抖店页面结构复杂，CSS 选择器不稳定，snapshot 更可靠。

```
data/raw/2026-06-15/
├── dashboard-overview.md    # 3016 bytes — 体验分、实时指标、7日趋势、渠道、618、诊断
├── orders-summary.md        # 1702 bytes — 今日订单表格、昨日摘要
├── products-summary.md      # 1074 bytes — 商品列表
└── aftersales-summary.md    #  614 bytes — 售后情况
```

**为什么是 Markdown 而非 JSON？**

Skill 文档中定义了结构化 JSON 格式（用 `browser_evaluate` 执行 JS 提取），但：
1. 抖店页面 DOM 结构复杂，类名不稳定，JS 提取容易失败
2. Playwright 的 `browser_snapshot` 返回的是可访问性树快照，格式稳定
3. LLM 阅读 Markdown 快照后在上下文中直接分析，比解析 JSON 更灵活
4. 实际数据量小（每日几十条订单），不需要严格的数据库格式

---

## 环节 3：分析与诊断 (`douyin-daily-analysis` Phase 2-3)

| 项目 | 内容 |
|------|------|
| **触发** | 需要完整运营分析 |
| **执行者** | LLM 自身（在上下文中推理），不依赖 Python 脚本 |
| **输入** | `data/raw/YYYY-MM-DD/` 下的 Markdown 文件 |
| **输出** | 分析结论（用于后续报告生成） |
| **状态** | ✅ 已可用（靠 LLM 推理） / ⚠️ Python 脚本为框架 |

### 关键发现：Python 脚本未实际使用

**这是理解整个工作流的关键。** `scripts/` 下的分析脚本定义了框架，但实际分析逻辑由 LLM 在上下文中完成。原因：

| 脚本 | 实际状态 | 说明 |
|------|---------|------|
| `analyze_daily.py` | 🔶 框架 | `calculate_base_metrics()` 函数体是 `TODO` 注释，实际计算在 LLM 上下文中完成 |
| `diagnose_problems.py` | 🔶 框架 | `diagnose()` 函数返回空列表 + `TODO` 注释，实际诊断在 LLM 上下文中完成 |
| `generate_report.py` | 🔶 模板 | `generate_daily_report()` 生成占位符模板，实际内容在 LLM 上下文中填充 |
| `generate_action_plan.py` | 🔶 模板 | `parse_problems()` 返回空列表 + `TODO` |
| `generate_future_recommendations.py` | 🔶 模板 | `load_data()` 函数体是 `pass` |
| `sync_douyin_to_feishu.py` | ✅ 生产 | **唯一的例外** — 773 行完整实现，解析日报 Markdown → 推飞书 |

### 诊断规则（来自 `docs/metrics_rules.md`）

LLM 在上下文中使用以下规则判断异常：

```
🔴 严重（今天必须处理）
  • 退款率 > 行业均值 × 1.5
  • GMV 环比下降 > 30%
  • 广告 ROI < 1（亏损）
  • 流量环比下降 > 30%

🟡 注意（本周处理）
  • GMV 环比下降 15%-30%
  • 转化率环比下降 > 20%
  • 单品销量集中度 > 80%
  • 退款率连续 3 天上涨

🟢 观察（持续关注）
  • GMV 环比下降 < 15%
  • 新上架商品（需要 1-2 周数据积累）
```

### 实际分析输出（2026-06-15 示例）

LLM 从 `dashboard-overview.md` 中自动识别出 3 个问题：

1. 🔴 **退款率严重恶化** — 7日 24.63%，当日 26.13%，5天恶化 8pp
2. 🔴 **转化率持续走低** — 3.74%，仅为同行 33%
3. 🟡 **过度依赖搜索+单爆品** — 搜索占比 51%，商品卡下滑 35%

每个问题包含：数据依据、可能原因（排序）、验证方法、解决方案表格（含负责人）、新手解释、3/7/30 天建议。

---

## 环节 4：报告生成 (`douyin-daily-analysis` Phase 4-6)

### 产出的 4 份报告

```
output/reports/
├── YYYY-MM-DD-daily-report.md          # 日报（核心指标+流量结构+商品健康度）
├── YYYY-MM-DD-diagnosis.md             # 诊断报告（3 个问题深度分析）
├── YYYY-MM-DD-action-plan.md           # 行动清单（优先级排序的任务表）
└── YYYY-MM-DD-future-recommendations.md # 未来建议（3/7/30天展望）
```

### 日报结构（2026-06-15 实际输出）

```markdown
# 抖店日报 — 2026-06-15
店铺信息 + 体验分 + 排名

## 一句话总结
[一句话概括最重要的发现]

## 核心指标
### 今日实时 — 12 个指标表格（含环比+同行基准+评价）
### 7日趋势 — 8 个指标
### 与上周对比 — 9 个指标的 5 天变化

## 流量结构 — 各渠道 GMV 占比

## 商品健康度 — 商品总数+爆品+滞销品
```

### 诊断报告结构（2026-06-15 实际输出）

```markdown
# 运营问题诊断报告 — 2026-06-15

## 今日最重要的 3 个问题

### 问题 N：标题 + 优先级/严重度 emoji
**数据依据：** [具体数字支撑]
**可能原因：** [按可能性排序，5 条]
**建议验证方法：** [如何确认原因]
**具体解决方案：** [表格：方案+效果+难度+负责人]
**新手解释：** [通俗语言]
**未来 3/7/30 天建议**

## 风险评估 — 4 个风险项（严重度+紧迫度+趋势）
```

---

## 环节 5：飞书同步

### 同步脚本 (`sync_douyin_to_feishu.py`)

| 项目 | 内容 |
|------|------|
| **状态** | ✅ 生产就绪（773 行） |
| **用法** | `python scripts/sync_douyin_to_feishu.py [YYYY-MM-DD]` |
| **依赖** | `mcp-servers/feishu/feishu_client.py` |
| **输入** | `output/reports/YYYY-MM-DD-daily-report.md` + `YYYY-MM-DD-diagnosis.md` |
| **输出** | 飞书多维表格 3 张表 |

### 推送的 3 张飞书表

```
表 1: 抖音每日指标表 (tblK15Duu70dPX6G)
  ├── 40+ 个结构化字段（GMV/订单/客单价/退款/曝光/转化/渠道/评分/商品...）
  ├── 从日报 Markdown 中用正则解析
  ├── 策略: Upsert（同一天覆盖写入）
  └── 数字类型字段，可在飞书中画图表

表 2: 抖音每日问题追踪表 (tblOZGoovyt8qb0I)
  ├── 每个问题一行（当天 3 个问题）
  ├── 字段: 标题/优先级/数据依据/业务影响/根因分析/解决建议/新手解释/状态
  ├── 策略: 先删当天旧数据，再写入新数据
  └── 可追踪解决状态

表 3: 抖音行动建议明细表 (tblPj7sBL74M07dN)
  ├── 每条建议独立一行（当天 ~15 条）
  ├── 字段: 关联问题/优先级/建议动作/为什么这样做/状态
  ├── 策略: 先删当天旧数据，再写入新数据
  └── 可追踪执行状态
```

### 解析能力

脚本用正则从日报 Markdown 中提取：
- **40+ 指标**：GMV、订单数、客单价、退款率、曝光、点击率、转化率、渠道 GMV、评分、商品健康度等
- **变化百分比**：处理 `↑86.69%`、`↑87.48%`、`持平` 等格式
- **文本摘要**：一句话总结、漏斗概况、渠道亮点、明日关注（清洗 Markdown → 纯文本）
- **退款原因 TOP 排行**：从百分比格式中提取原因文本和占比
- **问题诊断**：从 `### 问题 N：` 格式中解析标题、优先级、数据依据、方案表格

---

## 完整数据流向

```
                        抖店后台 (fxg.jinritemai.com)
                                  │
                    Playwright MCP (browser_snapshot)
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  data/raw/YYYY-MM-DD/    │
                    │  ├── dashboard-overview.md│  ← 首页仪表盘快照
                    │  ├── orders-summary.md    │  ← 订单页快照
                    │  ├── products-summary.md  │  ← 商品页快照
                    │  └── aftersales-summary.md│  ← 售后页快照
                    └────────────┬────────────┘
                                 │
                    LLM 读取 + 在上下文中分析
                    (不依赖 Python 脚本)
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
            daily-report.md  diagnosis.md  action-plan.md
            (日报)           (诊断报告)     (行动清单)
                    │            │            │
                    └────────────┼────────────┘
                                 │
                    sync_douyin_to_feishu.py
                    正则解析 Markdown → 结构化字段
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
              表1: 每日指标   表2: 问题追踪   表3: 行动建议
              (40+字段)      (每问题一行)    (每条建议一行)
```

---

## 两套分析路径对比

项目中实际上有**两套并行的分析路径**，它们的差异是理解架构的关键：

| 维度 | 路径 A：LLM 直接分析 | 路径 B：Python 脚本分析 |
|------|---------------------|------------------------|
| **数据格式** | Markdown 快照（实际在用） | JSON 结构化（skill 文档定义，未实现） |
| **分析执行者** | LLM 在上下文中推理 | `analyze_daily.py` 等脚本 |
| **灵活性** | 高（适应页面变化） | 低（依赖固定字段映射） |
| **可复现性** | 低（每次 LLM 推理结果不同） | 高（脚本输出确定） |
| **当前状态** | ✅ 实际使用 | 🔶 框架就绪，逻辑 TODO |
| **优势** | 能理解上下文，适应新格式 | 速度稳定，可审计，可定时运行 |
| **劣势** | 消耗 tokens，可能有幻觉 | 需要维护解析规则 |

### 当前实务

实际工作流是**路径 A（LLM 直接分析）**：

1. Playwright 截取页面快照 → 保存为 Markdown
2. LLM 读取 Markdown → 在上下文中计算指标、诊断问题
3. LLM 直接写出报告 Markdown
4. `sync_douyin_to_feishu.py` 解析报告 Markdown → 推飞书

Python 脚本（`analyze_daily.py`、`diagnose_problems.py` 等）定义了数据结构、模板和接口约定，但核心计算逻辑未实现。

---

## 两个速览入口 vs 完整流程

```
用户需求
    │
    ├── "快速扫一眼" ──→ douyin-quick-check (~2 min)
    │                   只看仪表盘核心指标卡
    │                   纯文本输出，不保存文件
    │
    └── "完整分析"  ──→ douyin-daily-analysis (~15-20 min)
                        完整 6 步流程
                        数据采集 → 分析 → 诊断 → 报告
                        产出 4 份报告文件
                        可选：同步到飞书
```

---

## 安全边界

所有环节都遵循**全程只读**原则：

| 环节 | 允许 | 禁止 |
|------|------|------|
| 登录 | 输入凭证，点击登录按钮 | — |
| 数据采集 | `browser_snapshot`、`browser_screenshot`、`browser_evaluate`（只读 JS） | 点击任何修改按钮（编辑/删除/上架/下架/改价） |
| 分析 | 读取本地文件，在内存中计算 | 调用写 API |
| 报告 | 写入本地 Markdown 文件 | 自动执行店铺操作 |
| 飞书同步 | 读取报告文件 → 写入飞书表格 | 删除飞书文档/表格（同步脚本会删当天旧数据再写新数据，但限于同一日期的 upsert） |

---

## 已知问题 & 待补齐项

| 问题 | 影响 | 建议 |
|------|------|------|
| Python 分析脚本是框架/TODO | 分析依赖 LLM 上下文，消耗 tokens，不可复现 | 补齐 `analyze_daily.py` 的 `calculate_base_metrics()` 和 `diagnose_problems.py` 的 `diagnose()` |
| 数据格式是 Markdown 快照非 JSON | 无法用脚本批量处理历史数据 | 两种选择：继续用 Markdown（务实），或实现 `douyin-fetch-data` 中定义的 JS 提取逻辑 |
| 无历史趋势数据库 | 环比只能靠 LLM 从报告中读取，无法自动跨天对比 | 补齐 `data/processed/` 的指标存储 + 趋势分析 |
| 采集依赖浏览器交互 | 页面改版会导致快照格式变化 | 快照格式比 DOM 选择器稳定，风险可控 |
| `douyin-quick-check` 和 `douyin-daily-analysis` 有功能重叠 | 两个 skill 都涉及看仪表盘 | 可以接受——quick-check 是轻量入口，daily-analysis 是完整流程 |

---

## 关键文件索引

```
Skills:                           Python 脚本:                      数据 & 输出:
.claude/skills/                   scripts/                          data/raw/YYYY-MM-DD/
  douyin-login/SKILL.md             analyze_daily.py    🔶框架        dashboard-overview.md
  douyin-quick-check/SKILL.md       diagnose_problems.py 🔶框架        orders-summary.md
  douyin-fetch-data/SKILL.md        generate_report.py   🔶模板        products-summary.md
  douyin-daily-analysis/SKILL.md    generate_action_plan.py 🔶模板     aftersales-summary.md
                                     generate_future_               output/reports/
文档:                                  recommendations.py 🔶模板       YYYY-MM-DD-daily-report.md
docs/metrics_rules.md               sync_douyin_to_feishu.py ✅生产    YYYY-MM-DD-diagnosis.md
                                                                     YYYY-MM-DD-action-plan.md
飞书:                                                               YYYY-MM-DD-future-recommendations.md
Base: GPFtbIOhCafB4HsANmVcbFOan4f                                  output/daily_summaries/
  表1: tblK15Duu70dPX6G (每日指标)                                    YYYY-MM-DD-summary.md
  表2: tblOZGoovyt8qb0I (问题追踪)
  表3: tblPj7sBL74M07dN (行动建议)
```

---

*文档由 orchestrator-agent 基于代码审查 + 实际产出物分析生成。*
