#!/usr/bin/env python3
"""
Run the full real footage pipeline for a given task.

Usage:
  python scripts/run_real_footage_pipeline.py input/tasks/example_task

Chains:
  analyze_footage.py   → output/footage_summary.md
  create_viral_plan.py → output/viral_plan.md
  create_voiceover.py  → output/voiceover_15s/30s/60s.txt
  create_subtitles.py  → output/subtitles.srt
  create_edit_plan.py  → output/edit_plan.md

Stops at edit_plan.md. Does NOT call TTS or Jianying.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_TASK = "example_task"

STEPS = [
    ("analyze_footage.py", "分析素材"),
    ("create_viral_plan.py", "生成爆点方向"),
    ("create_voiceover.py", "生成 AI 口播稿"),
    ("create_subtitles.py", "生成字幕"),
    ("create_edit_plan.py", "生成剪辑方案"),
]


def main():
    task_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TASK
    task_dir = Path(f"input/tasks/{task_name}")

    print("=" * 60)
    print(f"  Pipeline: real_footage_ai_voiceover_jianying")
    print(f"  Task: {task_name}")
    print("=" * 60)

    for script_name, label in STEPS:
        script = SCRIPTS_DIR / script_name
        if not script.exists():
            print(f"[SKIP] {script_name} not found")
            continue

        print(f"\n[STEP] {label}")
        result = subprocess.run([sys.executable, str(script), str(task_dir)])
        if result.returncode != 0:
            print(f"[FAIL] {script_name} 退出码 {result.returncode}")
            sys.exit(1)

    out_dir = task_dir / "output"
    print(f"\n完成。产物在 {out_dir}/")
    print("下一步：审核后接入 jianying-editor-skill 生成成片")


if __name__ == "__main__":
    main()
