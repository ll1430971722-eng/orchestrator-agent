"""Generate a pre-signed URL for an existing TOS object."""
import sys
from pathlib import Path
import tos
from dotenv import load_dotenv
import os


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_tos_signed_url.py <tos_key> [expiry_seconds]")
        sys.exit(1)

    tos_key = sys.argv[1]
    expiry = int(sys.argv[2]) if len(sys.argv) > 2 else 86400  # 24 hours default

    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    required = ["TOS_ACCESS_KEY", "TOS_SECRET_KEY", "TOS_BUCKET", "TOS_REGION", "TOS_ENDPOINT"]
    config = {}
    for key in required:
        val = os.getenv(key)
        if not val:
            raise ValueError(f"Missing {key} in .env")
        config[key] = val

    client = tos.TosClientV2(
        ak=config["TOS_ACCESS_KEY"],
        sk=config["TOS_SECRET_KEY"],
        endpoint=config["TOS_ENDPOINT"],
        region=config["TOS_REGION"],
    )

    bucket = config["TOS_BUCKET"]

    signed_url = client.generate_presigned_url(
        Method="GET",
        Bucket=bucket,
        Key=tos_key,
        ExpiresIn=expiry,
    )

    print(f"Signed URL ({expiry}s expiry):")
    print(signed_url)

    return signed_url


if __name__ == "__main__":
    main()
