---
description: 飞书文档/表格/消息/日历/知识库操作指南，通过内置飞书MCP Server完成。当需要同步到飞书、发飞书消息、更新飞书表格时使用。
disable-model-invocation: true
---
## 用途

飞书操作指南 — 通过 feishu MCP Server 完成文档/表格/消息/日历/知识库操作。

## 触发条件

- 用户说"同步到飞书"、"发飞书消息"、"更新飞书表格"
- 用户说"查飞书文档"、"飞书日历"
- 每日分析流程中自动触发

## MCP 工具概览

飞书操作通过 `mcp__feishu__*` 系列工具完成，覆盖 6 个域共 31 个工具。

### 文档操作
- 创建/读取/追加/搜索/删除文档
- 文档 ID 从飞书 URL 提取：`https://xxx.feishu.cn/docx/<doc_id>`

### 多维表格 (Bitable)
- 读/写记录、创建表、查询字段
- App Token 从 URL 提取：`https://xxx.feishu.cn/base/<app_token>`

### 消息
- 发消息到用户/群聊/Webhook
- 查消息历史

### 日历
- 查日历/日程、创建日程

### 知识库
- 搜索/浏览知识库节点

### 云盘 & 审批
- 查文件列表、搜索文件
- 查审批列表/详情

## 飞书资源映射

| 资源 | ID | 说明 |
|------|-----|------|
| Base | `GPFtbIOhCafB4HsANmVcbFOan4f` | 运营数据主 Base |
| 每日运营概览表 | `tbldtOCO6pR5g7bP` | 一天一条完整概览 |
| 每日运营追踪表 | `tblLck1taVRaxldS` | 协同动作 & 待办 |
| 抖音每日指标表 | `tblK15Duu70dPX6G` | douyin 结构化指标 |
| 抖音每日问题追踪表 | `tblOZGoovyt8qb0I` | 问题诊断+原因+建议 |
| 抖音行动建议明细表 | `tblPj7sBL74M07dN` | 建议独立行，追踪执行 |

## 同步脚本

```bash
# 同步 douyin 指标到飞书
python scripts/sync_douyin_to_feishu.py YYYY-MM-DD

# 同步 orchestrator 聚合概览到飞书
python scripts/sync_to_feishu.py YYYY-MM-DD

# 同步今天（默认）
python scripts/sync_douyin_to_feishu.py
python scripts/sync_to_feishu.py
```

脚本自动处理：概览表覆盖写入（同日只保留最新），追踪表追加写入（保留历史）。

## 安全铁律

1. **绝对禁止删除**飞书文档、表格、知识库节点
2. **始终追加**，不覆盖已有内容（概览表同日覆盖除外）
3. 未经确认不 @人
4. 不在日志/报告中打印密钥
5. 写入前告知用户：写什么、写到哪

## 常用工作流

### 同步日报到飞书
1. 确保日报已生成（`output/reports/` 或 `output/daily_summaries/`）
2. `python scripts/sync_douyin_to_feishu.py YYYY-MM-DD`
3. `python scripts/sync_to_feishu.py YYYY-MM-DD`
4. 确认同步结果

### 发飞书消息通知
1. 确认消息内容和目标（群/人/Webhook）
2. 使用 `mcp__feishu__send_message` 发送
3. 记录到 `memory/daily-log.md`

### 查询飞书表格数据
1. 使用 `mcp__feishu__read_bitable` 读取
2. 需要时导出为 JSON 存到 `data/from_feishu/`
