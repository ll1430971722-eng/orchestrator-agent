---
description: 使用Seedance AI根据参考素材生成视频，支持reference_to_video模式。当brief中generation_mode为reference_to_video时触发。
disable-model-invocation: false
---

# seedance-reference-video

## 用途

用于 `reference_to_video` 模式，即用户提供参考素材，让 Seedance 根据参考素材生成新的 AI 视频。参考素材不会出现在最终视频中，仅作为 AI 生成的视觉参考。

## 什么时候使用

- `brief.txt` 中 `video_type: ai_generated` 且 `generation_mode: reference_to_video`
- 用户说「结合素材生成」
- 用户说「参考样品间视频」
- 用户觉得上一版没有结合素材

### 自动触发条件

当任务的 `status.json` 中 `route` 为 `seedance_generation` 且 `generation_mode` 为 `reference_to_video`，且 `stage` 为 `route_decided` 时，自动调用本 skill。

## 输入信息

- `input/tasks/<任务名>/assets/` — 参考视频或图片素材
- `input/tasks/<任务名>/reference_materials.json` — TOS 上传后的 signed URL
- `.env` 中的 Seedance 配置
- `.env` 中的 TOS 配置（如需上传本地素材）

## 执行步骤

1. 检查 `assets/` 是否有视频或图片素材。
2. 检查 `reference_materials.json` 是否存在、是否包含有效的 signed URL。
3. 如果没有 `reference_materials.json`：
   - 说明本地路径不能直接给 Seedance 使用
   - 检查是否已有 TOS 上传能力（`.env` 中是否有 TOS 配置）
   - 如果需要上传，先 dry-run 确认上传参数
   - 询问用户确认后再上传
4. 如果素材过大（视频超过 Seedance 限制），先压缩参考视频。
5. 上传到 TOS 后生成 signed URL。
6. 写入 `reference_materials.json`，记录 URL 和过期时间。
7. 生成 Seedance prompt，必须明确引用 reference video URL。
8. 在调用 Seedance 前，必须确认请求体中真的使用了 reference video URL。
9. 如果不能确认 reference video URL 被传入，**不要调用 Seedance**。
10. 调用 Seedance 后下载生成视频。
11. 输出到 `output/pending_review/`。

## 重要规则

- **不能把本地路径假装成公网 URL**
- **不能只根据文字 prompt 假装参考了素材**
- 如果没有 signed_url 或可访问 URL，**必须停止并说明原因**
- 如果 Seedance reference video 有大小限制，需要先压缩
- 不要打印完整 signed URL（只打印 URL 域名和路径前缀）
- 不要打印任何密钥
- 不要自动发布

## 输出要求

输出文件列表：

- `reference_materials.json` — TOS signed URL 记录
- `seedance_prompt.txt` — 使用到的 Seedance prompt
- `generated_video.mp4` — 生成并下载的视频
- `status.txt` — 当前状态
- `review_checklist.txt` — 审核清单

## 常见失败情况

- `assets/` 没有素材
- `reference_materials.json` 不存在
- signed URL 过期
- 视频太大超过限制
- TOS 配置缺失（`.env` 中无相关配置）
- Seedance 请求体没有正确传 reference video URL
- 生成比例不是 9:16

## status.json 更新

本 skill 执行完毕后，必须更新任务目录下的 `status.json`：
- 设置 `stage` 为 `final_video_rendered`
- 将 `stages.final_video_rendered` 状态设为 `completed`
- 更新 `output_files.generated_video` 为视频路径
- 更新 `updated_at` 时间戳

## 验证清单

- [ ] 是否真的使用了 reference video URL（检查请求体）
- [ ] 是否没有使用本地路径冒充 URL
- [ ] 是否输出了 `reference_materials.json`
- [ ] 是否生成并下载了视频
- [ ] 是否输出到了正确的 `pending_review` 目录
- [ ] 是否没有打印 signed URL 或密钥
- [ ] 是否更新了 `status.json`
