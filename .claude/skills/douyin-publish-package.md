---
disable-model-invocation: false
---

# douyin-publish-package

## 用途

视频生成后，整理抖音待审核发布包。将所有发布所需素材、文案、元数据打包到统一目录，供人工审核后发布。

## 什么时候使用

- 视频已经生成完毕
- 用户准备审核视频
- 用户需要标题、文案、封面文案、置顶评论、标签
- 用户要发抖音但还没人工审核

### 自动触发条件

当任务的 `status.json` 中 `stage` 为 `final_video_rendered`（status: completed）且 `publish_package_created` 为 `pending` 时，自动调用本 skill 生成发布包。

## 输入信息

- `generated_video.mp4` — 已生成的视频文件
- `seedance_prompt.txt` — 使用的 Seedance prompt
- `content_plan.md` — 内容规划（如有）
- 用户指定平台和账号
- 用户指定视频目标

## 输出目录格式

```
output/pending_review/抖音/<账号名>/<任务名>/
```

## 发布包内容

发布包至少包含以下文件：

| 文件 | 说明 |
|------|------|
| `generated_video.mp4` | 视频文件 |
| `seedance_prompt.txt` | 使用的 Seedance prompt |
| `content_plan.md` | 内容规划 |
| `title.txt` | 视频标题 |
| `caption.txt` | 发布文案/描述 |
| `hashtags.txt` | 标签列表（每行一个） |
| `cover_text.txt` | 封面文案 |
| `pinned_comment.txt` | 置顶评论 |
| `comment_options.txt` | 评论区互动选项 |
| `publish_target.json` | 发布目标信息（平台、账号、时间等） |
| `review_checklist.txt` | 人工审核清单 |
| `status.txt` | 当前状态（初始值：`pending_review`） |

## 执行步骤

1. 确认视频已生成且位于正确路径。
2. 确认目标平台和账号（如用户未指定，询问确认）。
3. 创建输出目录 `output/pending_review/抖音/<账号名>/<任务名>/`。
4. 复制/移动视频文件到发布包目录。
5. 根据 `seedance_prompt.txt` 和 `content_plan.md` 生成配套文案：
   - 标题（吸引眼球、含关键词）
   - 发布文案（适合抖音风格）
   - 标签（热门标签 + 行业标签）
   - 封面文案（大字标题）
   - 置顶评论（引导互动）
   - 评论区选项（预准备的互动回复）
6. 编写 `publish_target.json`，包含目标平台、账号、发布时间窗口等信息。
7. 编写 `review_checklist.txt`（见下方详细内容）。
8. 设置 `status.txt` 为 `pending_review`。

## review_checklist.txt 必须包含

```
- [ ] 视频是否符合目标账号定位
- [ ] 是否适合抖音竖屏（9:16）
- [ ] 是否有前 3 秒钩子（吸引停留）
- [ ] 是否有明确评论引导
- [ ] 是否有标题和封面
- [ ] 是否有置顶评论
- [ ] 是否有发布文案
- [ ] 是否有风险点（侵权、敏感词、违规内容）
- [ ] 是否需要重新生成
```

## 重要规则

- **不要自动发布**
- **不要登录抖音后台**
- **不要点击发布按钮**
- **不要修改线上账号**
- 只生成待审核发布包
- 用户必须人工审核后才能发布
- `status.txt` 初始状态必须为 `pending_review`

## 常见失败情况

- 视频文件缺失或路径错误
- 用户未指定目标平台和账号
- 文案不符合抖音调性
- 标签不适配目标受众

## 验证清单

- [ ] 是否生成了完整发布包（所有文件齐全）
- [ ] 是否**没有**自动发布
- [ ] 是否输出路径正确（`output/pending_review/抖音/<账号名>/<任务名>/`）
- [ ] 是否包含 `publish_target.json`
- [ ] 是否 `status.txt` 为 `pending_review`
- [ ] 是否所有文案适合抖音平台
