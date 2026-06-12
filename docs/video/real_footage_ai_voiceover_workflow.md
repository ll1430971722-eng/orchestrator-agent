# 真实素材 + AI 口播 + 剪映 Skill 线

## 路线名称

real_footage_ai_voiceover_jianying

## 适用条件

- `video_route` 为 `auto` 且 `input/current_task/assets/` 有素材
- 或 `video_type` 为 `real_footage`
- 用户拍摄了真实视频素材，但不想录音、不想现场口播

## 目标

用户拍真实素材，Agent 读懂素材，自动生成：
- 素材摘要
- 短视频爆点方向
- AI 口播稿（15s / 30s / 60s）
- 字幕文件（SRT）
- 剪辑方案
- 剪映草稿或成片

## 完整流程

```
1. 用户准备素材
   │  从 materials_library 挑选素材
   │  复制到 input/current_task/assets/
   │
2. 填写 brief.txt                 input/current_task/brief.txt
   │
3. 判断路线                        scripts/decide_video_route.py
   │                                → 选择 real_footage_ai_voiceover_jianying
   │
4. 分析素材                        scripts/analyze_footage.py
   │   ffprobe 获取元信息
   │   ffmpeg 抽关键帧
   │   输出 footage_summary.md
   │
5. 生成爆点方向                    scripts/create_viral_plan.py
   │   结合平台/账号/主题
   │   生成 3 个方向，含钩子和评分
   │   输出 viral_plan.md
   │
6. 生成 AI 口播稿                  scripts/create_voiceover.py
   │   根据最高分方向生成
   │   3 个时长版本
   │   输出 voiceover_15s/30s/60s.txt
   │
7. 生成字幕                        scripts/create_subtitles.py
   │   按句子分配时间轴
   │   输出 subtitles.srt
   │
8. 生成剪辑方案                    scripts/create_edit_plan.py
   │   整合以上所有分析
   │   输出 edit_plan.md
   │
9. 生成剪映草稿                    scripts/create_jianying_draft.py
   │   调用 jianying-editor-skill
   │   [第一版占位，暂不实际操作剪映]
   │
10. 审核                           output/pending_review/
                                    → approved / rejected / published
```

## 工具分工

| 工具 | 职责 | 当前状态 |
|------|------|----------|
| ffmpeg / ffprobe | 读取视频元信息、抽帧 | 脚本已就绪 |
| claude-video-vision | AI 读懂视频素材内容 | 后续接入 |
| TTS 服务 | voiceover.txt → voiceover.mp3 | 第一版占位，不调用付费接口 |
| jianying-editor-skill | 生成剪映草稿或成片 | 后续接入 |

## 重要规则

- 不自动发布
- 不删除原始素材
- 第一版先生成文档、框架和占位脚本
- 不立即安装外部插件
- 后续再接入 claude-video-vision 和 jianying-editor-skill
- 每次做视频只处理 `input/current_task/assets/` 下的素材

## 串联运行

```bash
# 运行完整流程（到 edit_plan.md 为止）
python scripts/run_real_footage_pipeline.py
```

Pipeline 会依次调用 analyze_footage → create_viral_plan → create_voiceover → create_subtitles → create_edit_plan，所有中间产物输出到 `input/current_task/analysis/`。
