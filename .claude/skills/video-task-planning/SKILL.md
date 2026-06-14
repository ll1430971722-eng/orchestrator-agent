---
description: 视频任务规划入口，决定视频路线和生成模式。任何视频任务开始前先进行规划。当用户要生成新视频或处理视频任务时使用。
disable-model-invocation: false
---

# video-task-planning

## 用途

任何视频任务开始前，先进行任务规划。这是所有视频任务的入口 Skill。

## 什么时候使用

- 用户要生成新视频
- 用户要修改已生成视频
- 用户提供了素材
- 用户要求生成抖音发布包
- 用户想切换视频路线

### 自动触发条件

当 video-agent 启动或空闲时，扫描 `input/tasks/` 目录，如果发现任何任务目录下存在 `brief.txt` 但**没有** `status.json`，自动调用本 skill 进行任务规划。

## 输入信息

优先读取以下文件：

- `input/tasks/<任务名>/brief.txt`
- `input/tasks/<任务名>/assets/`
- `input/tasks/<任务名>/reference_materials.json`
- `output/pending_review/` 下已有结果

## 执行步骤

1. 识别任务路径。如果用户未指定任务名，列出 `input/tasks/` 下现有任务让用户选择。
2. 读取 `brief.txt`，提取 `video_type`、`generation_mode`、`video_route` 等关键字段。
3. 检查 `assets/` 是否有素材文件（视频、图片）。
4. 检查 `reference_materials.json` 是否存在。
5. 根据 Route Decision Rules 判断视频路线：
   - `text_to_video`：无素材文字生成 → seedance_generation
   - `reference_to_video`：有参考素材的 AI 视频生成 → seedance_generation
   - `real_footage_edit`：真实素材剪辑 → real_footage_ai_voiceover_jianying
6. 输出任务计划，不要立刻执行。
7. 计划里必须说明以下内容：
   - 目标平台（抖音等）
   - 目标账号
   - 视频主题
   - 视频路线
   - 是否需要上传素材到 TOS
   - 是否会调用付费 API（Seedance）
   - 预计输出目录
   - 风险点（素材缺失、配置缺失、URL 过期等）
   - 下一步建议

## 安全边界

- 不要直接调用 Seedance API
- 不要直接上传 TOS
- 不要自动发布视频
- 不要删除原始素材
- 不要覆盖已有生成结果
- 如果任务信息不足，先列出需要用户确认的问题，不要猜测

## status.json 管理

本 skill 执行完毕后，必须在任务目录下创建 `status.json`：

```json
{
  "task_name": "<任务名>",
  "status": "planned",
  "stage": "route_decided",
  "route": "<seedance_generation|real_footage_ai_voiceover_jianying>",
  "generation_mode": "<text_to_video|reference_to_video|real_footage_edit>",
  "created_at": "<ISO 8601 timestamp>",
  "updated_at": "<ISO 8601 timestamp>",
  "stages": {
    "brief_loaded": {"status": "completed", "timestamp": "<now>"},
    "route_decided": {"status": "completed", "timestamp": "<now>"},
    "footage_analyzed": {"status": "pending", "timestamp": null},
    "viral_plan_generated": {"status": "pending", "timestamp": null},
    "voiceover_generated": {"status": "pending", "timestamp": null},
    "tts_generated": {"status": "pending", "timestamp": null},
    "subtitles_generated": {"status": "pending", "timestamp": null},
    "edit_plan_generated": {"status": "pending", "timestamp": null},
    "final_video_rendered": {"status": "pending", "timestamp": null},
    "publish_package_created": {"status": "pending", "timestamp": null},
    "published": {"status": "pending", "timestamp": null}
  },
  "errors": [],
  "output_files": {},
  "orchestrator_context": {}
}
```

- `route` 为 `seedance_generation` 时，跳过 `footage_analyzed`、`viral_plan_generated`、`voiceover_generated` 阶段（设为 `skipped`）
- `route` 为 `real_footage_ai_voiceover_jianying` 时，Seedance 相关阶段设为 `skipped`
- 如果 brief.txt 中包含 `orchestrator_context` 信息（由 orchestrator-agent 写入），保留到 `orchestrator_context` 字段

## 输出要求

- 输出一个清晰的执行计划，用中文
- 如果用户明确要求「直接执行」，也必须先完成基础检查，再执行
- 计划中必须标明哪些步骤需要用户确认
- **必须创建 `status.json`** 文件到任务目录

## 常见失败情况

- `brief.txt` 不存在或格式不正确
- `assets/` 目录为空
- 用户未指定任务名称
- 无法判断视频路线（`video_type: auto` 且有素材）

## 验证清单

- [ ] 是否识别了正确任务目录
- [ ] 是否读取了 `brief.txt`
- [ ] 是否判断了素材状态
- [ ] 是否判断了正确视频路线
- [ ] 是否说明了是否需要用户确认
- [ ] 是否没有直接调用 Seedance / TOS / 发布
