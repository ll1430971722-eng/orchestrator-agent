# Orchestrator Agent

三个业务 agent 的上级编排者。统一协调 douyin-shop-agent、stationery-market-agent、video-agent 的日常工作。

## 子 Agent

| Agent | 职责 | 路径 |
|-------|------|------|
| douyin-shop-agent | 抖音店铺运营分析（只读） | `../douyin-shop-agent/` |
| stationery-market-agent | 文具笔袋市场洞察 | `../stationery-market-agent/` |
| video-agent | 视频内容生产 | `../video-agent/` |

## 使用方式

在此项目目录下启动 Claude Code，然后说：

- `开始今日分析` — 触发每日编排流程
- `看看各 agent 今天做了什么` — 快速检查各 agent 产出
- `本周回顾` — 生成本周运营回顾
- `有什么跨 agent 的机会` — 分析协同机会

## 设计原则

- **编排不替代**：只协调子 agent，不重复实现它们的逻辑
- **读 output，写 input**：通过文件系统与子 agent 交互
- **人工确认**：所有协同动作先告知用户再执行
