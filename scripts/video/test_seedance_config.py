"""Test script to verify Seedance configuration without making generation requests.

Only checks environment variables — no API calls, no billing risk.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seedance_client import load_config


def main():
    print("Testing Seedance 2.0 configuration...\n")

    try:
        config = load_config()
    except ValueError as e:
        print(f"  FAIL: {e}")
        print("  Create a .env file from .env.example and set ARK_API_KEY.")
        return False

    checks = [
        ("ARK_API_KEY", config["api_key"], lambda v: len(v) > 0),
        ("ARK_BASE_URL", config["base_url"], lambda v: v.startswith("https://")),
        ("SEEDANCE_MODEL", config["model"], lambda v: len(v) > 0),
    ]

    all_ok = True
    for name, value, check in checks:
        ok = check(value)
        status = "  OK" if ok else "FAIL"
        print(f"  [{status}] {name} = {value[:20] + '...' if len(value) > 20 else value}")
        if not ok:
            all_ok = False

    print()
    if all_ok:
        print("Configuration is valid. No API calls were made.")
    else:
        print("Configuration check failed. Review .env settings.")

    return all_ok


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
