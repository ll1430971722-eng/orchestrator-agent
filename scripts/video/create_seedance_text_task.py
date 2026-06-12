"""Submit a Seedance 2.0 text-to-video generation task.

Default (no --run): prints the request that would be sent.
With --run: actually calls the API (incurs billing).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seedance_client import load_config, create_video_task

TEST_PROMPT = (
    "生成一条 10 秒竖屏短视频，画面是一个年轻人在办公室对着镜头讲话，"
    "风格真实自然，适合短视频平台，镜头稳定，字幕区域留白。"
)


def main():
    parser = argparse.ArgumentParser(
        description="Submit a Seedance 2.0 text-to-video task"
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Actually call the API (default: dry-run, print request only)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=TEST_PROMPT,
        help="Custom text prompt (default: built-in test prompt)",
    )
    args = parser.parse_args()

    config = load_config()

    url = f"{config['base_url']}/contents/generations/tasks"
    payload = {
        "model": config["model"],
        "content": [{"type": "text", "text": args.prompt}],
    }

    if not args.run:
        print("=== DRY RUN (use --run to submit) ===\n")
        print(f"POST {url}\n")
        print("Headers:")
        print(f"  Authorization: Bearer {config['api_key'][:20]}...")
        print(f"  Content-Type: application/json\n")
        print("Body:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print()
        return

    print("=== Submitting task ===\n")
    print(f"POST {url}\n")
    print(f"Prompt: {args.prompt}\n")

    try:
        result = create_video_task(args.prompt, config=config)
        print(f"\nTask submitted. Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"\nTask submission failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
