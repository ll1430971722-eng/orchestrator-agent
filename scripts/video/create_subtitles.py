#!/usr/bin/env python3
"""
Generate subtitles.srt from voiceover text.

Usage:
  python scripts/create_subtitles.py input/tasks/example_task

Outputs subtitles.srt into task/output/.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASK = "example_task"


def format_ts(s: float) -> str:
    h, m = int(s // 3600), int((s % 3600) // 60)
    sec, ms = int(s % 60), int((s % 1) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def main():
    task_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TASK
    output_dir = PROJECT_ROOT / "input" / "tasks" / task_name / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Pick the first available voiceover
    vo_path = None
    for f in sorted(output_dir.glob("voiceover_*.txt")):
        vo_path = f
        break
    if not vo_path:
        print("[WARN] 没有 voiceover 文件，先运行 create_voiceover.py")
        return

    print(f"[INFO] 使用: {vo_path.name}")
    text = vo_path.read_text(encoding="utf-8")
    # Strip header line like 【30s】
    text = re.sub(r'^【.*?】\n?', '', text.strip())

    # Split into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[。！？.!?])', text) if s.strip()]
    # Further split long sentences
    expanded = []
    for s in sentences:
        subs = [x.strip() for x in re.split(r'(?<=[，,；;：:])', s) if x.strip()]
        expanded.extend(subs)

    # Determine duration from filename
    dur = 30.0
    if "15s" in vo_path.name:
        dur = 15.0
    elif "60s" in vo_path.name:
        dur = 60.0

    per = dur / len(expanded) if expanded else 1.0
    lines = []
    for i, sent in enumerate(expanded):
        lines.append(str(i + 1))
        lines.append(f"{format_ts(i * per)} --> {format_ts(min((i + 1) * per, dur))}")
        lines.append(sent)
        lines.append("")

    out = output_dir / "subtitles.srt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] {out} ({len(expanded)} 条字幕, ~{dur}s)")


if __name__ == "__main__":
    main()
