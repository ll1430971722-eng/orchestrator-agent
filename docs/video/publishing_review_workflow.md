# 审核发布流程

## 核心规则

所有视频生成后**必须先进入** `output/pending_review/`，由用户人工审核后再决定下一步。

## 状态流转

```
output/pending_review/         待审核
       │
       ├──→ output/approved/   审核通过，准备发布
       ├──→ output/rejected/   审核不通过
       └──→ output/published/  已发布到目标平台
```

## 状态说明

| 状态 | 目录 | 含义 |
|------|------|------|
| pending_review | `output/pending_review/` | 刚生成，等待用户审核 |
| approved | `output/approved/` | 用户确认通过，可以手动发布 |
| rejected | `output/rejected/` | 用户认为不行，需修改或放弃 |
| published | `output/published/` | 已发布到目标平台（抖音/小红书/视频号等） |

## 审核流程

1. Agent 生成视频 → 自动保存到 `output/pending_review/`
2. 用户打开 `output/pending_review/` 查看视频
3. 用户决定：
   - **通过** → 移动到 `output/approved/`，准备发布
   - **不通过** → 移动到 `output/rejected/`，根据原因调整 brief 或素材后重新生成
   - **发布** → 手动发布到平台后，移动到 `output/published/`
4. 记录到 `materials_library/metadata/usage_log.csv`

## 不自动发布

- Agent 不会自动将视频发布到任何平台
- 发布操作由用户手动完成
- 发布后由用户将视频文件移到 `output/published/`

## 多轮修改

如果审核不通过：
1. 用户说明原因（如口播不自然、节奏不对、素材选得不好）
2. 更新 `brief.txt` 或调整素材
3. 重新运行对应路线
4. 新视频再次进入 `pending_review`
