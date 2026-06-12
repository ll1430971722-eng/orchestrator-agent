#!/usr/bin/env python3
"""
Analyze video footage in the current task's assets/ folder.

Usage:
  python scripts/analyze_footage.py input/tasks/example_task

Uses ffprobe for metadata and ffmpeg to extract keyframes.
Outputs footage_summary.md into the task's output/ directory.

Does NOT delete or modify original files.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASK = "example_task"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".avi"}


def check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_video_files(assets_dir: Path) -> list[Path]:
    if not assets_dir.exists():
        return []
    return sorted(f for f in assets_dir.iterdir()
                   if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS)


def get_video_info(video_path: Path) -> dict:
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
           "-show_format", "-show_streams", str(video_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    info = {"file_name": video_path.name, "duration_s": 0, "width": 0,
            "height": 0, "fps": 0, "has_audio": False, "file_size_mb": 0}
    info["file_size_mb"] = round(video_path.stat().st_size / (1024 * 1024), 2)

    for stream in data.get("streams", []):
        if stream["codec_type"] == "video":
            info["width"] = stream.get("width", 0)
            info["height"] = stream.get("height", 0)
            fps_str = stream.get("r_frame_rate", "0/1")
            if "/" in fps_str:
                n, d = fps_str.split("/")
                info["fps"] = round(float(n) / float(d), 2) if float(d) != 0 else 0
        elif stream["codec_type"] == "audio":
            info["has_audio"] = True

    dur = float(data.get("format", {}).get("duration", 0))
    info["duration_s"] = round(dur, 1)
    return info


def extract_keyframes(video_path: Path, frames_dir: Path, interval_s: int = 3) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(frames_dir / f"{video_path.stem}_frame_%03d.jpg")
    cmd = ["ffmpeg", "-i", str(video_path), "-vf", f"fps=1/{interval_s}",
           "-q:v", "2", "-y", pattern]
    subprocess.run(cmd, capture_output=True)
    return len(list(frames_dir.glob(f"{video_path.stem}_frame_*.jpg")))


def main():
    if not check_ffmpeg():
        print("[ERROR] ffmpeg/ffprobe 未安装。brew install ffmpeg")
        sys.exit(1)

    task_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TASK
    task_dir = PROJECT_ROOT / "input" / "tasks" / task_name
    assets_dir = task_dir / "assets"
    output_dir = task_dir / "output"
    frames_dir = output_dir / "frames"
    output_dir.mkdir(parents=True, exist_ok=True)

    video_files = get_video_files(assets_dir)
    if not video_files:
        print("[WARN] assets/ 中没有视频文件")
        return

    print(f"[INFO] 找到 {len(video_files)} 个视频")

    lines = ["# 素材分析报告", "", f"**任务：** {task_name}", f"**素材数：** {len(video_files)}", "", "---", ""]
    total_dur = 0

    for vf in video_files:
        print(f"[INFO] 分析: {vf.name}")
        info = get_video_info(vf)
        total_dur += info["duration_s"]

        lines.extend([
            f"## {info['file_name']}",
            f"- 大小: {info['file_size_mb']} MB",
            f"- 时长: {str(timedelta(seconds=int(info['duration_s'])))} ({info['duration_s']}s)",
            f"- 分辨率: {info['width']}×{info['height']}",
            f"- 帧率: {info['fps']} fps",
            f"- 有音频: {'是' if info['has_audio'] else '否'}",
            "",
        ])

        interval = max(2, int(info["duration_s"] / 5)) if info["duration_s"] > 5 else 2
        n = extract_keyframes(vf, frames_dir, interval)
        if n > 0:
            lines.append(f"- 抽帧: {n} 张 → output/frames/")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend([
        "## 整体摘要",
        f"- 总时长: {str(timedelta(seconds=int(total_dur)))}",
        "",
        "## 使用建议",
        "（由 Agent 在后续步骤中补充）",
    ])

    md_path = output_dir / "footage_summary.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] 报告: {md_path}")


if __name__ == "__main__":
    main()
