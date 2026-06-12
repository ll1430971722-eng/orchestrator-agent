"""Upload a local file to 火山引擎 TOS and return the public URL.

Uses the official tos SDK (volcengine TOS Python SDK).
"""

import os
import sys
from pathlib import Path

import tos
from dotenv import load_dotenv


def load_tos_config() -> dict:
    """Load TOS credentials from .env."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    required = ["TOS_ACCESS_KEY", "TOS_SECRET_KEY", "TOS_BUCKET", "TOS_REGION", "TOS_ENDPOINT"]
    config = {}
    for key in required:
        val = os.getenv(key)
        if not val:
            raise ValueError(f"缺少 {key}，请在 .env 中配置")
        config[key] = val
    return config


def upload_to_tos(local_path: str, tos_key: str = None, config: dict = None) -> str:
    """Upload a file to TOS and return the public URL."""
    if config is None:
        config = load_tos_config()

    local_file = Path(local_path)
    if not local_file.exists():
        raise FileNotFoundError(f"文件不存在: {local_path}")

    if tos_key is None:
        tos_key = local_file.name

    file_size_mb = local_file.stat().st_size / (1024 * 1024)
    print(f"准备上传: {local_file.name} ({file_size_mb:.1f} MB)")

    # Create TOS client
    client = tos.TosClientV2(
        ak=config["TOS_ACCESS_KEY"],
        sk=config["TOS_SECRET_KEY"],
        endpoint=config["TOS_ENDPOINT"],
        region=config["TOS_REGION"],
    )

    bucket = config["TOS_BUCKET"]
    print(f"上传到: {bucket}/{tos_key}")

    # Upload with progress
    with open(local_path, "rb") as f:
        result = client.put_object(
            bucket=bucket,
            key=tos_key,
            content=f,
        )

    print(f"上传成功! status={result.status_code}, etag={result.etag}")

    # Construct public URL
    public_url = f"https://{bucket}.tos-{config['TOS_REGION']}.volces.com/{tos_key}"
    print(f"公网 URL: {public_url}")
    return public_url


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/upload_asset_to_tos.py <local_file_path> [tos_key]")
        sys.exit(1)

    local_path = sys.argv[1]
    tos_key = sys.argv[2] if len(sys.argv) > 2 else None

    config = load_tos_config()
    url = upload_to_tos(local_path, tos_key, config)
    print(f"\n✅ 上传完成")
    print(f"URL: {url}")


if __name__ == "__main__":
    main()
