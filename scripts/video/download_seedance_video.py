"""Download a completed Seedance 2.0 video by task ID.

Usage:
    python3 scripts/download_seedance_video.py <task_id> <output_path>

Example:
    python3 scripts/download_seedance_video.py cgt-20260526235731-2vrc4 output/test.mp4
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seedance_client import load_config, get_task_status, download_video


def main():
    parser = argparse.ArgumentParser(
        description="Download a completed Seedance 2.0 video"
    )
    parser.add_argument(
        "task_id",
        type=str,
        help="Task ID (e.g. cgt-20260526235731-2vrc4)",
    )
    parser.add_argument(
        "output_path",
        type=str,
        help="Local path to save the video (e.g. output/test.mp4)",
    )
    args = parser.parse_args()

    config = load_config()

    print(f"=== Querying task: {args.task_id} ===\n")
    try:
        result = get_task_status(args.task_id, config=config)
    except Exception as e:
        print(f"\nQuery failed: {e}")
        sys.exit(1)

    status = result.get("status")
    if status != "succeeded":
        print(f"\nTask is not ready. status={status}")
        sys.exit(1)

    content = result.get("content", {})
    video_url = content.get("video_url") if isinstance(content, dict) else None

    if not video_url:
        print("\nvideo_url not found in response. Full response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    print(f"\nTask succeeded. Downloading video...")
    print(f"  URL: {video_url[:120]}...")

    try:
        saved = download_video(video_url, args.output_path)
        print(f"\nSaved to: {saved}")
    except Exception as e:
        print(f"\nDownload failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
