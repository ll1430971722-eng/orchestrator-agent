#!/usr/bin/env python3
"""
Generate edit plan for Jianying.

Usage:
  python scripts/create_edit_plan.py input/tasks/example_task

Outputs edit_plan.md into task/output/.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASK = "example_task"


def parse_brief(text: str) -> dict:
    data: dict = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if v:
                data[k] = v
    return data


def main():
    task_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TASK
    task_dir = PROJECT_ROOT / "input" / "tasks" / task_name
    output_dir = task_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    brief_text = (task_dir / "brief.txt").read_text(encoding="utf-8") if (task_dir / "brief.txt").exists() else ""
    brief = parse_brief(brief_text)
    topic = brief.get("topic", "待定主题")
    platform = brief.get("target_platform", "待定平台")
    account = brief.get("target_account", "待定账号")
    dur = brief.get("target_duration", "30s")

    md = f"""# 剪辑方案

## 基本信息
- **主题：** {topic}
- **平台：** {platform} | **账号：** {account}
- **时长：** {dur}

## 开头钩子
- 前3秒：黑底白字抛出核心问题 / 反常识观点
- 切第一个素材镜头，口播同步进入

## 素材顺序

| 时间 | 内容 | 备注 |
|------|------|------|
| 0:00-0:03 | 标题卡片 + 钩子画面 | 大号加粗 |
| 0:03-0:15 | 主要过程素材 | 可加速1.2x |
| 0:15-0:25 | 细节/对比素材 | |
| 0:25-{dur} | 结尾卡片 + 引导关注 | |

## 字幕风格
- 白字黑边，底部居中
- 钩子句大号加粗，正文常规
- 逐字出现或淡入

## 节奏
- 3-5秒切一个画面，硬切为主
- BGM 电子/轻量，音量低于口播 -12dB

## 平台适配
- {platform}：竖屏 9:16，前3秒决定完播率，字幕必加

## 剪映执行
后续由 jianying-editor-skill 自动：导入素材 → 排列时间线 → 添加字幕 → 添加口播 → 导出
"""

    out = output_dir / "edit_plan.md"
    out.write_text(md, encoding="utf-8")
    print(f"[OK] {out}")


if __name__ == "__main__":
    main()
