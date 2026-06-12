# Seedance 参考素材生成视频工作流

## 两种生成模式

Seedance AI 视频生成线支持两种模式：

| 模式 | generation_mode | assets/ | 说明 |
|------|-----------------|---------|------|
| 纯文字生成 | `text_to_video` | 空 | 仅根据 brief.txt 生成 AI 视频 |
| 参考素材生成 | `reference_to_video` | 放入参考图/视频 | 素材作为 Seedance 参考，生成新的 AI 视频 |

## reference_to_video 流程

用户提供参考图片或视频，Agent 先读懂素材，再结合平台、账号和爆点方法优化 Seedance prompt，最终生成新的 AI 视频。注意：素材只作为参考，用于指导 Seedance 生成风格/构图/氛围相似的视频，不是对原素材做剪辑。

### 完整步骤

```
1. 创建任务文件夹
       │
2. 填写 brief.txt
   video_type: ai_generated
   generation_mode: reference_to_video
       │
3. 放入参考素材到 assets/
   图片：.jpg .png .webp
   视频：.mp4 .mov .m4v
       │
4. 运行 decide_video_route.py
       │  确认选择 seedance_generation
       │  确认 generation_mode 为 reference_to_video
       │
5. Agent 分析参考素材
   图片：读取内容、风格、色调、构图
   视频：ffprobe 获取元信息 + ffmpeg 抽帧
   输出素材摘要到 task/output/
       │
6. Agent 生成 3 个视频创意方向
   结合 brief.txt 的主题/平台/账号/风格
   每个方向包含：
     - 方向名称
     - 前 3 秒画面描述
     - 整体视觉风格
     - 与参考素材的关联点
     - 评分（满分 10）
   输出到 task/output/viral_plan.md
       │
7. 选择最推荐的创意方向
       │
8. 生成 Seedance prompt
   基于选定的方向 + 参考素材特征
   prompt 应包含：
     - 主体描述
     - 场景/环境
     - 风格/色调/光影
     - 动作/运镜
     - 时长期望
     - 参考素材的视觉特征
       │
9. 调用 Seedance API 创建任务
   python scripts/create_seedance_text_task.py --prompt "..." --run
       │
10. 查询任务状态
    python scripts/check_seedance_task.py --task-id <id>
        │
11. 下载生成视频
    python scripts/download_seedance_video.py --task-id <id>
    保存到 task/output/ 和 output/pending_review/
        │
12. 用户审核
    output/pending_review/ → approved / rejected
```

## brief.txt 配置示例

```ini
target_platform: 抖音
target_account: 科技生活号
video_route: auto
video_type: ai_generated
generation_mode: reference_to_video
topic: 智能工厂数字孪生展示
material_description: 几张工厂车间实拍照片，色调偏冷，光线较暗，设备为银色金属
desired_style: 科技感、未来感、3D 数字孪生效果
publishing_goal: 展示技术能力，吸引企业客户咨询
target_duration: 15s
output_language: zh
```

## 与 text_to_video 的区别

| | text_to_video | reference_to_video |
|--|---------------|-------------------|
| 输入 | 只有文字 | 文字 + 参考图/视频 |
| prompt 来源 | 完全靠想象力描述 | 结合参考素材的实际视觉特征 |
| 生成结果 | 随机性较大 | 更贴合用户已有的视觉风格 |
| 适用场景 | 没有视觉参考，只要大概方向对就行 | 有确定的品牌/账号视觉风格，要保持一致 |

## 与 real_footage 的区别

| | reference_to_video | real_footage_edit |
|--|-------------------|-------------------|
| 素材角色 | 参考，不直接使用 | 主体，直接剪辑进正片 |
| 输出 | AI 生成的新视频 | 原始素材 + 口播 + 字幕 |
| 声音 | AI 可能生成背景音 | 需要 TTS 生成 AI 口播 |
| 适用 | 需要新画面但保持风格一致 | 素材本身内容就是主体 |
