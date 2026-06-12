# Seedance AI 生成视频线

## 路线名称

seedance_generation

## 适用条件

- `video_route` 为 `auto` 且 `input/current_task/assets/` 无素材
- 或 `video_type` 为 `ai_generated`
- 用户没有真实视频素材，需要 AI 生成视频

## 完整流程

```
1. 用户填 brief.txt           input/current_task/brief.txt
       │
2. 判断路线                    scripts/decide_video_route.py
       │                         → 选择 seedance_generation
       │
3. Agent 生成 Seedance prompt   根据平台/账号/主题/风格
       │                         生成符合 Seedance API 的 prompt
       │
4. 调用 API 创建任务            scripts/create_seedance_text_task.py
       │                         POST /contents/generations/tasks
       │
5. 查询任务状态                 scripts/check_seedance_task.py
       │                         GET /contents/generations/tasks/{task_id}
       │                         轮询直到 completed 或 failed
       │
6. 下载生成视频                 scripts/download_seedance_video.py
       │                         保存到 output/pending_review/
       │
7. 审核                         output/pending_review/
                                 → approved / rejected / published
```

## API 信息

| 配置项 | 值 |
|--------|-----|
| ARK_BASE_URL | https://ark.cn-beijing.volces.com/api/v3 |
| SEEDANCE_MODEL | doubao-seedance-2-0-260128 |
| 创建任务接口 | POST /contents/generations/tasks |
| 查询任务接口 | GET /contents/generations/tasks/{task_id} |

配置存储在项目根目录 `.env` 文件中。

## 已有脚本（不要修改）

| 脚本 | 功能 |
|------|------|
| `scripts/seedance_client.py` | 核心客户端：创建任务、查询状态、下载视频 |
| `scripts/create_seedance_text_task.py` | 文字生成视频任务创建（支持 --dry-run） |
| `scripts/check_seedance_task.py` | 查询任务状态 |
| `scripts/download_seedance_video.py` | 下载生成视频到 output/pending_review/ |
| `scripts/test_seedance_config.py` | 测试配置是否正确（不扣费） |

## 使用示例

```bash
# 1. 测试配置
python scripts/test_seedance_config.py

# 2. 创建任务（先 dry-run 查看 prompt，确认后再真正执行）
python scripts/create_seedance_text_task.py --prompt "your prompt here" --dry-run
python scripts/create_seedance_text_task.py --prompt "your prompt here" --run

# 3. 查询任务状态
python scripts/check_seedance_task.py --task-id <task_id>

# 4. 下载视频
python scripts/download_seedance_video.py --task-id <task_id>
```
