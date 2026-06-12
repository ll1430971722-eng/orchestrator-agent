# 轻量任务制工作流

## 核心思路

每条视频一个任务文件夹。三种模式覆盖所有场景。

## 三种任务模式

| 模式 | video_type | generation_mode | assets/ | 走哪条路线 |
|------|-----------|-----------------|---------|-----------|
| 无素材 AI 生成 | `ai_generated` | `text_to_video` | 空 | seedance_generation |
| 参考素材 AI 生成 | `ai_generated` | `reference_to_video` | 放参考图/视频 | seedance_generation |
| 真实素材剪辑 | `real_footage` | `real_footage_edit` | 放素材 | real_footage_ai_voiceover_jianying |

## 任务文件夹结构

```
input/tasks/<任务名>/
├── brief.txt          # 任务说明
├── assets/            # 素材（可选）
├── output/            # 中间产物
└── route_plan.json    # 路线判断（自动生成）
```

## 工作流程

### 1. 创建任务、填写 brief

复制 `example_task`，编辑 `brief.txt`：

```
# 模式一：无素材 AI 生成
video_type: ai_generated
generation_mode: text_to_video
# assets/ 留空

# 模式二：参考素材 AI 生成
video_type: ai_generated
generation_mode: reference_to_video
# 把参考图片/视频放入 assets/

# 模式三：真实素材剪辑
video_type: real_footage
generation_mode: real_footage_edit
# 把素材放入 assets/
```

### 2. 判断路线

```bash
python scripts/decide_video_route.py input/tasks/<任务名>
```

| 情况 | 结果 |
|------|------|
| video_type: ai_generated + no assets | → seedance (text_to_video) |
| video_type: ai_generated + has assets | → seedance (reference_to_video) |
| video_type: real_footage | → real_footage_ai_voiceover_jianying |
| auto + 有素材 + 没写 video_type | → 提示用户选择 A 或 B |

### 3. 走对应路线

**AI 生成线（模式一 / 模式二）：**

```bash
# 创建 Seedance 任务
python scripts/create_seedance_text_task.py --prompt "..." --run

# 查询状态
python scripts/check_seedance_task.py --task-id <id>

# 下载视频
python scripts/download_seedance_video.py --task-id <id>
```

模式二在生成 prompt 前，Agent 会先分析参考素材的视觉特征。

**真实素材剪辑线（模式三）：**

```bash
python scripts/run_real_footage_pipeline.py input/tasks/<任务名>
```

产出：素材摘要 → 爆点方向 → 口播稿 → 字幕 → 剪辑方案。

### 4. 审核

所有视频 → `output/pending_review/` → 人工审核 → approved / rejected / published。

不自动发布。

## 重要区别

- `reference_to_video`：素材作为**参考**，生成**新的** AI 视频，原始素材不直接出现在成片中
- `real_footage_edit`：素材作为**主体**，直接剪辑进成片，加上 AI 口播和字幕
- 不要在 reference_to_video 模式下把素材拿去剪辑
- 也不要在 real_footage_edit 模式下拿素材去生成 AI 视频
