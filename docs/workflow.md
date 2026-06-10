# Orchestrator Agent 工作流详解

## 日常运营工作流

### 每日节奏

```
09:00  检查 market-agent 数据是否就绪（B站脚本自动跑，其他需人工导出）
10:00  触发 market-agent 每日分析
10:30  触发 shop-agent 每日分析
11:00  聚合两份报告，生成每日概览
11:30  识别协同机会，决定是否创建视频任务
```

### 触发方式

1. 在各子 agent 目录下启动 Claude Code，按对应 CLAUDE.md 的指引操作
2. 回到 orchestrator-agent，说"聚合今日报告"
3. orchestrator 读取子 agent 产出，生成统一概览

## 跨 Agent 协同场景

### 场景 1: 市场发现爆款 → 快速出视频

**触发**: market-agent 日报中出现 A 级证据的爆款趋势
**动作**:
1. orchestrator 确认趋势值得跟进
2. 在 video-agent/input/tasks/ 创建拍摄任务 brief
3. 告知用户："市场发现 X 趋势，已为 video-agent 创建任务，请去 video-agent 执行"

### 场景 2: 店铺商品转化异常 → 竞品对标

**触发**: shop-agent 日报显示某商品转化率连续下降
**动作**:
1. orchestrator 建议用户让 market-agent 重点分析该品类竞品
2. 如有竞品数据，交叉分析找出差距

### 场景 3: 视频发布后 → 效果追踪

**触发**: video-agent 有新的待审核视频产出
**动作**:
1. orchestrator 记录发布计划
2. 视频发布 N 天后，提醒用户在 shop-agent 查看流量和转化变化
3. 对比视频发布前后的数据，评估内容效果

### 场景 4: 周度回顾

**触发**: 用户说"本周回顾"
**动作**:
1. 收集本周所有每日概览
2. 收集 shop-agent 周度数据趋势
3. 收集 market-agent 周度趋势
4. 收集 video-agent 本周产出列表
5. 交叉分析，产出周度回顾报告

## 数据流

```
    市场数据                    店铺数据
       │                          │
       ▼                          ▼
stationery-market-agent    douyin-shop-agent
       │                          │
       ├── 日报 ──┐          ┌── 日报
       │          │          │
       ├── 选题 ──┤          ├── 行动清单
       │          │          │
       │          ▼          │
       │    orchestrator     │
       │          │          │
       │    每日统一概览     │
       │          │          │
       ▼          │          ▼
   video-agent    │    人工执行
       │          │
       └── 视频 ──┘
```

## 人工环节说明

以下环节仍需人工操作（orchestrator 无法自动化）：

1. **导出市场数据**: 1688/抖音电商罗盘的数据需要人工从卖家后台导出 CSV
2. **上传视频素材**: video-agent 需要的实拍素材需人工准备
3. **执行店铺操作**: shop-agent 给出的行动清单需人工在抖店后台执行
4. **发布视频**: video-agent 产出的视频需人工审核后发布到抖音
5. **启动子 agent**: 各子 agent 需要在各自目录下启动 Claude Code
