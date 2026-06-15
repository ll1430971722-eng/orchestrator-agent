---
description: 工作树分身完成汇报 — 结束时自动调用，写入结构化同步记录到共享 memory。保证主 Agent 能收集所有分身的产出。
disable-model-invocation: true
---

## 触发条件

任何 worktree 分身结束任务时调用。CLAUDE.md 规则要求分身结束时必须执行。

## 功能

将本次分身的工作内容写入共享 memory，让主 orchestrator 能收集汇总。

## 步骤

### Step 1: 确认身份

确认当前 worktree 名称：
```bash
git rev-parse --abbrev-ref HEAD
```

### Step 2: 收集本次工作内容

从 git log 和文件系统中收集：
- 本次 commit 做了什么（`git log master..HEAD --oneline`）
- 产出了什么文件（`output/` 下的新文件）
- 有什么待审核产出（`output/pending_review/` 下的内容）

### Step 3: 写入同步记录

写入 JSON 到 `memory/sync-records/YYYY-MM-DD-<worktree名>.json`：

```json
{
  "worktree": "worktree/market-20260615",
  "date": "2026-06-15",
  "completed_at": "2026-06-15T10:30:00",
  "type": "market-analysis",
  "summary": "竞品分析：潼辉文化用品企业店",
  "commits": ["competitor analysis: 潼辉文化"],
  "outputs": ["output/reports/competitor-analysis-0615.md"],
  "pending_review": [],
  "status": "completed",
  "notes": ""
}
```

### Step 4: 追加到 daily-log

在 `memory/daily-log.md` 末尾追加：

```markdown

## YYYY-MM-DD

### <worktree名>
- 完成时间: HH:MM
- 工作内容: <summary>
- 产出: <outputs 列表>
- 状态: ✅ 完成
```

### Step 5: 向用户汇报

```
📡 同步完成 → memory/sync-records/YYYY-MM-DD-<name>.json

本次分身产出:
  ✅ <产出1>
  ✅ <产出2>

主 Agent 下次汇总时能自动看到。
```

## 输出

- `memory/sync-records/YYYY-MM-DD-<worktree名>.json` — 结构化同步记录
- `memory/daily-log.md` — 追加一条日志

## 安全规则

- ✅ 只写入 memory/ 共享目录
- ❌ 不修改主项目的代码文件
