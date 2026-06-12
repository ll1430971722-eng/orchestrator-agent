#!/usr/bin/env python3
"""
Generate viral video plan for a task.

Usage:
  python scripts/create_viral_plan.py input/tasks/example_task

Reads brief.txt and footage_summary.md, outputs viral_plan.md into task/output/.
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
    brief_path = task_dir / "brief.txt"
    summary_path = task_dir / "output" / "footage_summary.md"
    output_dir = task_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    brief = parse_brief(brief_path.read_text(encoding="utf-8") if brief_path.exists() else "")
    topic = brief.get("topic", "待定主题")
    platform = brief.get("target_platform", "待定平台")
    account = brief.get("target_account", "待定账号")
    style = brief.get("desired_style", "")

    md = f"""# 短视频爆点方向分析

**主题：** {topic} | **平台：** {platform} | **账号：** {account} | **风格：** {style}

---

## 方向一：痛点切入 + 解决方案 (8/10)

**前3秒钩子：** "这个问题折磨了很久，直到用了这个方法……"

**内容结构：**
1. 0-3s 抛出痛点 → 2. 3-15s 展示传统做法的低效
3. 15-30s 展示新方法/新工具带来的变化 → 4. 结尾总结 + 引导互动

---

## 方向二：幕后过程 + 沉浸式记录 (7/10)

**前3秒钩子：** "很多人只看结果，不知道过程是这样的……"

**内容结构：**
1. 0-3s 结果画面吸引 → 2. 3-20s 倒叙完整过程
3. 20-35s 遇到的困难和解决方法 → 4. 结尾感悟

---

## 方向三：干货清单 + 快速输出 (8.5/10) ★ 推荐

**前3秒钩子：** "做 {topic} 一定要知道的3件事，第3个最重要……"

**内容结构：**
1. 0-3s 一句话概括价值 → 2. 3-10s 第一条干货
3. 10-20s 第二条干货 → 4. 20-35s 第三条（最重要的）
5. 结尾总结 + 引导收藏关注

---

## 选型建议

推荐**方向三**：收藏率高 → 算法推荐权重高，结构清晰、制作效率高。
"""

    out_path = output_dir / "viral_plan.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"[OK] {out_path}")


if __name__ == "__main__":
    main()
