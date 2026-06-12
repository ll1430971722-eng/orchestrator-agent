"""Query Seedance 2.0 task status by task ID.

Usage:
    python3 scripts/check_seedance_task.py <task_id>
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seedance_client import load_config, get_task_status


def main():
    parser = argparse.ArgumentParser(
        description="Query Seedance 2.0 video generation task status"
    )
    parser.add_argument(
        "task_id",
        type=str,
        help="Task ID to query (e.g. cgt-20260526235731-2vrc4)",
    )
    args = parser.parse_args()

    config = load_config()
    url = f"{config['base_url']}/contents/generations/tasks/{args.task_id}"

    print(f"=== Querying task: {args.task_id} ===\n")
    print(f"GET {url}\n")

    try:
        result = get_task_status(args.task_id, config=config)
        print(f"\n--- Formatted response ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\nQuery failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
