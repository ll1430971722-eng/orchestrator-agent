from __future__ import annotations

import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv


def load_config() -> dict:
    """Load configuration from .env file and return as dict."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        raise ValueError("ARK_API_KEY is not set in .env")

    return {
        "api_key": api_key,
        "base_url": os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        "model": os.getenv("SEEDANCE_MODEL", "doubao-seedance-2-0-260128"),
    }


def create_video_task(
    prompt: str,
    image_urls: list[str] | None = None,
    video_urls: list[str] | None = None,
    config: dict | None = None,
) -> dict:
    """Create a video generation task via Seedance 2.0 API.

    Args:
        prompt: Text description for video generation.
        image_urls: Optional list of reference image URLs.
        video_urls: Optional list of reference video URLs.
        config: Optional config dict from load_config(). Loads from .env if omitted.

    Returns:
        Response JSON containing task_id and status.
    """
    if config is None:
        config = load_config()

    url = f"{config['base_url']}/contents/generations/tasks"

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    payload: dict = {
        "model": config["model"],
        "content": [{"type": "text", "text": prompt}],
    }

    if image_urls:
        for img in image_urls:
            payload["content"].append({"type": "image_url", "image_url": {"url": img}})

    if video_urls:
        for vid in video_urls:
            payload["content"].append({
                "type": "video_url",
                "video_url": {"url": vid},
                "role": "reference_video",
            })

    resp = requests.post(url, json=payload, headers=headers, timeout=30)

    print(f"HTTP Status: {resp.status_code}")

    try:
        data = resp.json()
    except ValueError:
        print(f"Response (non-JSON): {resp.text}")
        resp.raise_for_status()
        return {}

    print(f"Response JSON: {data}")

    if not resp.ok:
        print(f"Request failed: {resp.status_code}")
        print(f"Response body: {data}")
        resp.raise_for_status()

    return data


def get_task_status(task_id: str, config: dict | None = None) -> dict:
    """Query the status of a video generation task."""
    if config is None:
        config = load_config()

    url = f"{config['base_url']}/contents/generations/tasks/{task_id}"

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    resp = requests.get(url, headers=headers, timeout=30)

    print(f"HTTP Status: {resp.status_code}")

    try:
        data = resp.json()
    except ValueError:
        print(f"Response (non-JSON): {resp.text}")
        resp.raise_for_status()
        return {}

    print(f"Response JSON: {data}")

    if not resp.ok:
        print(f"Request failed: {resp.status_code}")
        print(f"Response body: {data}")
        resp.raise_for_status()

    return data


def download_video(url: str, output_path: str) -> str:
    """Download a generated video from the given URL to output_path.

    Args:
        url: The video download URL.
        output_path: Local file path to save the video.

    Returns:
        The resolved output_path where the video was saved.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()

    with open(out, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return str(out.resolve())
