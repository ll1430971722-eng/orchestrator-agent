# Orchestrator Agent 工作流详解

## 架构原则

**单入口**：所有日常运营在 orchestrator-agent 一个窗口完成。不需要再切换多个 agent 项目。

- 抖店分析 → 内置 Skills + Playwright MCP
- 飞书操作 → 同窗口通过 feishu MCP Server
- 视频任务 → 给 video-agent 写 brief，它独立完成
- 每日汇总 → 同窗口生成并推飞书

## 日常运营工作流

### 每日节奏

```
09:00  说 /douyin-quick-check，快速扫一眼今天店铺概况
10:00  如需要完整日报，说 /douyin-daily-analysis
11:00  python scripts/sync_douyin_to_feishu.py（推指标到飞书）
11:30  检查 video-agent 产出，生成统一概览
       python scripts/sync_to_feishu.py（推概览到飞书）
```

### 触发方式（简化后）

1. 在 orchestrator-agent 目录下启动 Claude Code
2. 说"今日分析"或"/douyin-daily-analysis"
3. orchestrator 自动完成数据采集→分析→出报告→推飞书

**不再需要**在各子 agent 目录下分别启动 Claude Code。

## 跨 Agent 协同场景

### 场景 1: 店铺商品转化异常 → 视频补救

**触发**: 日报显示某商品转化率连续下降
**动作**:
1. orchestrator 分析是否有视频内容覆盖该商品
2. 如无对应视频，在 `../video-agent/input/tasks/` 创建拍摄任务 brief
3. 告知用户关注该商品后续数据

### 场景 2: 店铺爆款 → 快速出更多视频

**触发**: 日报显示某商品数据爆发
**动作**:
1. orchestrator 确认值得跟进
2. 在 `../video-agent/input/tasks/` 创建拍摄任务 brief
3. 通过 feishu MCP 同步信息到飞书

### 场景 3: 视频发布后 → 效果追踪

**触发**: video-agent 有新的待审核视频产出
**动作**:
1. orchestrator 记录发布计划
2. 视频发布 N 天后，在日报中对比发布前后数据
3. 评估内容效果

### 场景 4: 周度回顾

**触发**: 用户说"本周回顾"
**动作**:
1. 收集本周所有每日概览
2. 收集 douyin 周度数据趋势
3. 收集 video-agent 本周产出列表
4. 交叉分析，产出周度回顾报告
5. 通过 feishu MCP 推送到飞书

## 数据流

```
         抖店后台 (fxg.jinritemai.com)
              │
              ▼
    orchestrator (Playwright MCP)
              │
              ├── data/raw/         (原始采集数据)
              ├── data/processed/   (计算后指标)
              ├── output/reports/   (日报/诊断/行动清单)
              │
              ├── scripts/sync_douyin_to_feishu.py → 飞书多维表格
              ├── scripts/sync_to_feishu.py        → 飞书多维表格
              │
              └── 数据洞察 → ../video-agent/input/tasks/ (创建视频任务)
                                  │
                                  ▼
                            video-agent
                                  │
                                  └── output/pending_review/ (视频产出)
```

## 人工环节说明

以下环节仍需人工操作：

1. **抖店验证码**: 首次登录或登录过期时，可能需要手动完成验证码
2. **执行店铺操作**: 日报给出的行动清单需人工在抖店后台执行
3. **上传视频素材**: video-agent 需要的实拍素材需人工准备
4. **发布视频**: video-agent 产出的视频需人工审核后发布到抖音
5. **创建 video-agent 会话**: 给 video-agent 下发任务后，需要在 video-agent 目录启动 Claude Code 执行

## MCP 服务器

本项目使用两个 MCP 服务器：

| 服务器 | 用途 | 配置位置 |
|--------|------|---------|
| Playwright | 浏览器自动化，访问抖店后台 | `settings.local.json` (mcpServers.playwright) |
| Feishu Agent | 飞书全功能操作（31 工具） | `settings.local.json` (mcpServers.feishu-agent) |
