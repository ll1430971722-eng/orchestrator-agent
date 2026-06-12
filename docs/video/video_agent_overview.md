# Video Agent — 视频内容生产系统

## 总目标

video-agent 是一个视频内容生产系统。用户通过 ChatGPT 生成执行指令，再由 Claude Code 执行 video-agent，生成视频成品。

每条视频一个独立任务文件夹，轻量、无复杂素材库依赖。

## 三种任务模式

| 模式 | 素材需求 | AI 做什么 | 最终产出 |
|------|----------|-----------|----------|
| 无素材 AI 生成 | 无 | 根据 brief.txt 写 prompt → Seedance 生成 | AI 生成的视频 |
| 参考素材 AI 生成 | 图片/视频作为参考 | 分析素材视觉特征 → 优化 prompt → Seedance 生成 | 风格一致的新 AI 视频 |
| 真实素材剪辑 | 视频/图片作为主体 | 分析素材 → AI 口播 → 字幕 → 剪辑方案 → 剪映草稿 | 素材剪辑 + 口播 + 字幕的成片 |

## 两条路线

### 路线一：seedance_generation

通过火山方舟 Seedance 2.0 API 生成 AI 视频。

支持两种模式：
- **text_to_video**：纯文字描述生成视频，不需要任何素材
- **reference_to_video**：用户提供参考图片/视频，Seedance 据此生成风格一致的新视频

**状态：** 已跑通。

### 路线二：real_footage_ai_voiceover_jianying

用户提供真实素材，Agent 读懂素材后生成 AI 口播、字幕、剪辑方案，再通过剪映 Skill 生成草稿/成片。

**状态：** 框架已搭建。后续接入 claude-video-vision 和 jianying-editor-skill。

## 系统架构

```
video-agent/
├── input/tasks/<任务名>/       # 每条视频一个任务文件夹
│   ├── brief.txt               # 任务说明（含 video_type 和 generation_mode）
│   ├── assets/                 # 素材（可选）
│   ├── output/                 # 中间产物
│   └── route_plan.json         # 路线判断（自动生成）
│
├── output/                     # 统一输出审核区
│   ├── pending_review/         # 待审核
│   ├── approved/               # 审核通过
│   ├── rejected/               # 不通过
│   └── published/              # 已发布
│
├── scripts/                    # 工具脚本
└── docs/                       # 文档
```

## 路线判断逻辑

1. `video_type: ai_generated` → 总是走 seedance_generation（无论 assets 是否为空）
2. `video_type: real_footage` → 总是走 real_footage_ai_voiceover_jianying
3. `video_route` 明确指定 → 按指定路线执行
4. `auto` + 未指定 video_type + assets 为空 → 默认 seedance (text_to_video)
5. `auto` + 未指定 video_type + assets 有素材 → 提示用户选择 A 或 B

## 安全规则

- 不自动发布
- 不删除原始素材
- 不覆盖 .env
- 不破坏已跑通的 Seedance 脚本
- 所有视频先进入 output/pending_review
- assets/ 有素材不代表一定走剪辑线
