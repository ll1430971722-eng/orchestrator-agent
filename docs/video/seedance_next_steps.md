# Seedance 2.0 接入进度

## 已完成

### 文字生成视频任务创建

`scripts/seedance_client.py` — `create_video_task(prompt)` 已实现：

- 从 `.env` 读取 `ARK_API_KEY`、`ARK_BASE_URL`、`SEEDANCE_MODEL`
- 调用 `POST ${ARK_BASE_URL}/contents/generations/tasks`
- 请求体格式：`{"model": "...", "content": [{"type": "text", "text": prompt}]}`
- 打印 HTTP 状态码和响应 JSON，失败时打印完整错误信息

`scripts/create_seedance_text_task.py` — 测试脚本：

- 默认 dry-run 模式，只打印请求内容，不扣费
- 加 `--run` 才真正调用 API
- 支持 `--prompt` 自定义提示词

## 待完成

### 1. 查询任务状态接口

```
GET {ARK_BASE_URL}/contents/generations/tasks/{task_id}
```

需要确认：
- 返回的状态字段和状态值（pending / processing / succeeded / failed）
- 轮询间隔建议
- 是否需要处理任务排队/限流

### 2. 下载生成结果接口

任务成功后从响应中提取视频下载 URL，下载到本地。
`seedance_client.py` 中 `download_video()` 已预留框架，但需要确认：
- 任务完成响应中视频 URL 的具体字段名
- URL 有效期
- 是否需要鉴权下载

### 3. 本地素材上传方案

当前只支持 text prompt。需要支持本地上传图片/视频作为参考素材：

- 图生视频（image-to-video）：上传本地图片，获取公网 URL 后传入 `content`
- 视频生视频（video-to-video）：上传本地视频片段作为参考

需要确认：
- Seedance API 是否支持直接在请求中上传二进制文件
- 如果不支持，需要中间存储方案：本地上传 → 获取公网 URL → 传入 Seedance
- 公网 URL 方案候选：
  - 火山引擎 TOS（对象存储）
  - 临时公网图床
  - 在 Ark 平台内先上传素材获取 file_id，再传给 Seedance
