#!/usr/bin/env python3
"""
Generate AI voiceover scripts for a task.

Usage:
  python scripts/create_voiceover.py input/tasks/example_task

Outputs voiceover_15s.txt, voiceover_30s.txt, voiceover_60s.txt into task/output/.
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


def generate(topic: str, account: str, platform: str, duration: int) -> str:
    if duration == 15:
        return f"【15s】\n做{topic}一定要知道的3件事。第一，别只看表面。第二，别人的经验可以参考，你的场景你最清楚。第三——先跑通一个完整流程再优化。我是{account}，关注我。"
    elif duration == 30:
        return f"【30s】\n很多人问我{topic}怎么做。说实话一开始我也踩了很多坑——拿到素材直接剪，剪一半发现方向不对全白做。后来改了：先花10分钟看素材标注关键片段，确定主线再动手。这个习惯帮我省了一半后期时间。关注{account}，在{platform}分享实操经验。"
    else:
        return f"【60s】\n做{topic}这件事我花了很久才想明白。很多人一上来就问什么工具好用、什么参数合理，但这些都不是最重要的。关键是：做给谁看、放哪个平台、达到什么效果。三个问题没想清楚前，做什么都白费。\n\n拿我自己举例，刚开始做完发出去数据很差，复盘发现内容和{platform}用户习惯对不上。后来花了时间研究同类型账号——它们前三秒一定有个明确钩子。所以我现在每条视频之前先想：第一，让观众记住什么；第二，前三秒怎么钩住他；第三，结尾让他干什么。这三个有答案了，后面就是填空。\n\n我是{account}，在{platform}分享{topic}相关经验，欢迎关注。"


def main():
    task_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TASK
    task_dir = PROJECT_ROOT / "input" / "tasks" / task_name
    output_dir = task_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    brief_text = (task_dir / "brief.txt").read_text(encoding="utf-8") if (task_dir / "brief.txt").exists() else ""
    brief = parse_brief(brief_text)
    topic = brief.get("topic", "待定主题")
    account = brief.get("target_account", "待定账号")
    platform = brief.get("target_platform", "待定平台")

    for dur in [15, 30, 60]:
        p = output_dir / f"voiceover_{dur}s.txt"
        p.write_text(generate(topic, account, platform, dur), encoding="utf-8")
        print(f"[OK] {p}")


if __name__ == "__main__":
    main()
