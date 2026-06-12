#!/usr/bin/env python3
"""
Decide video production route for a task.

Usage:
  python scripts/decide_video_route.py input/tasks/example_task

Reads task/brief.txt, checks task/assets/, outputs task/route_plan.json.

Route logic:
  - video_type: ai_generated + generation_mode: text_to_video → seedance
  - video_type: ai_generated + generation_mode: reference_to_video → seedance
  - video_type: real_footage → real_footage_ai_voiceover_jianying
  - video_route: seedance_generation → seedance
  - video_route: real_footage_ai_voiceover_jianying → real_footage
  - auto + empty assets → seedance (text_to_video)
  - auto + has assets + no video_type → need_user_choice

Does NOT call any paid API.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASK = "example_task"
MEDIA_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".avi",
                    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

ROUTE_SEEDANCE = "seedance_generation"
ROUTE_REAL = "real_footage_ai_voiceover_jianying"


def parse_brief(path: Path) -> dict:
    data: dict = {}
    if not path.exists():
        print(f"[WARN] brief.txt not found at {path}")
        return data
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                key, value = key.strip(), value.strip()
                if value:
                    data[key] = value
    return data


def count_assets(assets_dir: Path) -> int:
    """Count media files in assets directory."""
    if not assets_dir.exists():
        return 0
    return sum(1 for f in assets_dir.iterdir()
               if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS)


def decide(brief: dict, asset_count: int) -> dict:
    """
    Apply route decision rules.
    Returns dict with selected_route, generation_mode, need_user_choice, etc.
    """
    video_route = brief.get("video_route", "auto")
    video_type = brief.get("video_type", "")
    generation_mode = brief.get("generation_mode", "")

    # ── 1. Explicit video_route overrides everything ──
    if video_route == ROUTE_SEEDANCE:
        mode = generation_mode if generation_mode else ("reference_to_video" if asset_count > 0 else "text_to_video")
        return {
            "selected_route": ROUTE_SEEDANCE,
            "generation_mode": mode,
            "reason": "brief.txt 中 video_route 指定为 seedance_generation",
            "need_user_choice": False,
        }

    if video_route == ROUTE_REAL:
        return {
            "selected_route": ROUTE_REAL,
            "generation_mode": "real_footage_edit",
            "reason": "brief.txt 中 video_route 指定为 real_footage_ai_voiceover_jianying",
            "need_user_choice": False,
        }

    # ── 2. video_type: ai_generated → always seedance ──
    if video_type == "ai_generated":
        mode = generation_mode if generation_mode in ("text_to_video", "reference_to_video") else (
            "reference_to_video" if asset_count > 0 else "text_to_video")
        resource_note = f"，assets/ 中有 {asset_count} 个素材，将作为 Seedance 参考素材" if asset_count > 0 else ""
        return {
            "selected_route": ROUTE_SEEDANCE,
            "generation_mode": mode,
            "reason": f"brief.txt 中 video_type 为 ai_generated，generation_mode 为 {mode}{resource_note}",
            "need_user_choice": False,
        }

    # ── 3. video_type: real_footage → real footage route ──
    if video_type == "real_footage":
        return {
            "selected_route": ROUTE_REAL,
            "generation_mode": "real_footage_edit",
            "reason": "brief.txt 中 video_type 为 real_footage",
            "need_user_choice": False,
        }

    # ── 4. auto + no video_type → detect ──
    if asset_count == 0:
        return {
            "selected_route": ROUTE_SEEDANCE,
            "generation_mode": "text_to_video",
            "reason": "assets/ 为空，默认走 Seedance AI 视频生成（text_to_video）",
            "need_user_choice": False,
        }
    else:
        return {
            "selected_route": "",
            "generation_mode": "",
            "reason": f"assets/ 中有 {asset_count} 个素材，但 video_type 未指定，需要用户选择",
            "need_user_choice": True,
            "user_choice_options": [
                {
                    "choice": "A",
                    "label": "素材作为 Seedance 参考，生成 AI 视频",
                    "brief_update": {
                        "video_type": "ai_generated",
                        "generation_mode": "reference_to_video",
                    },
                },
                {
                    "choice": "B",
                    "label": "素材作为主体，走真实素材剪辑路线",
                    "brief_update": {
                        "video_type": "real_footage",
                        "generation_mode": "real_footage_edit",
                    },
                },
            ],
        }


def main():
    task_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TASK
    task_dir = PROJECT_ROOT / "input" / "tasks" / task_name

    if not task_dir.exists():
        print(f"[ERROR] Task folder not found: {task_dir}")
        sys.exit(1)

    brief_path = task_dir / "brief.txt"
    assets_dir = task_dir / "assets"
    output_path = task_dir / "route_plan.json"

    brief = parse_brief(brief_path)
    asset_count = count_assets(assets_dir)

    print(f"[INFO] Task: {task_name}")
    print(f"[INFO] video_route: {brief.get('video_route', 'auto')}")
    print(f"[INFO] video_type: {brief.get('video_type', '(未指定)')}")
    print(f"[INFO] generation_mode: {brief.get('generation_mode', '(未指定)')}")
    print(f"[INFO] Assets: {asset_count} 个文件")

    decision = decide(brief, asset_count)

    route_plan = {
        "selected_route": decision["selected_route"],
        "generation_mode": decision["generation_mode"],
        "reason": decision["reason"],
        "target_platform": brief.get("target_platform", ""),
        "target_account": brief.get("target_account", ""),
        "topic": brief.get("topic", ""),
        "task_path": str(task_dir.resolve()),
        "has_assets": asset_count > 0,
        "asset_count": asset_count,
        "need_user_choice": decision.get("need_user_choice", False),
        "next_step": "",
    }

    if decision.get("need_user_choice"):
        route_plan["user_choice_options"] = decision["user_choice_options"]
        route_plan["next_step"] = (
            "用户需要选择 A 或 B，然后更新 brief.txt 中的 video_type 和 generation_mode，"
            "再重新运行本脚本"
        )
    elif route_plan["selected_route"] == ROUTE_SEEDANCE:
        if route_plan["generation_mode"] == "reference_to_video":
            route_plan["next_step"] = (
                "分析 assets/ 中的参考素材 → 生成 Seedance prompt → "
                "运行 scripts/create_seedance_text_task.py 创建视频生成任务"
            )
        else:
            route_plan["next_step"] = (
                "基于 brief.txt 生成 Seedance prompt → "
                "运行 scripts/create_seedance_text_task.py 创建视频生成任务"
            )
    else:
        route_plan["next_step"] = (
            "运行 scripts/run_real_footage_pipeline.py 串联 "
            "素材分析 → 爆点方向 → 口播 → 字幕 → 剪辑方案"
        )

    output_path.write_text(
        json.dumps(route_plan, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[RESULT] Route: {route_plan['selected_route'] or '(需要用户选择)'}")
    print(f"[RESULT] Generation: {route_plan['generation_mode'] or '(待定)'}")
    print(f"[RESULT] Reason: {route_plan['reason']}")
    if route_plan["need_user_choice"]:
        print(f"[RESULT] ⚠️  需要用户选择：")
        for opt in route_plan["user_choice_options"]:
            print(f"  {opt['choice']}: {opt['label']}")
    print(f"[RESULT] Next: {route_plan['next_step']}")
    print(f"[RESULT] Plan saved: {output_path}")


if __name__ == "__main__":
    main()
