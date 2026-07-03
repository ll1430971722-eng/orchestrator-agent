#!/usr/bin/env python3
"""
Orchestrator → 飞书多维表格 同步脚本

读取 output/daily_summaries/YYYY-MM-DD-summary.md，
将结构化内容写入飞书 Base:
  - 每日运营概览表 (tbldtOCO6pR5g7bP): 每日总览（覆盖写入）
  - 每日运营追踪表 (tblLck1taVRaxldS): 协同动作（追加）

用法:
  python scripts/sync_to_feishu.py 2026-06-09
  python scripts/sync_to_feishu.py            # 默认今天
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

# ---- Path Setup ----
ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ORCHESTRATOR_ROOT / "scripts"))
FEISHU_MCP = ORCHESTRATOR_ROOT / "mcp-servers" / "feishu"
sys.path.insert(0, str(FEISHU_MCP))

from feishu_client import get_client, FeishuAPIError
from config import (
    FEISHU_APP_TOKEN as APP_TOKEN,
    TABLE_DAILY_OVERVIEW as OVERVIEW_TABLE_ID,
    TABLE_DAILY_TRACKING as TRACKING_TABLE_ID,
    OUTPUT_DAILY_SUMMARIES as OUTPUT_DIR,
)


def parse_daily_summary(date_str: str) -> dict:
    """Parse the daily summary markdown into structured sections."""
    filepath = OUTPUT_DIR / f"{date_str}-summary.md"
    if not filepath.exists():
        print(f"❌ 日报文件不存在: {filepath}")
        sys.exit(1)

    content = filepath.read_text(encoding="utf-8")
    sections = _split_sections(content)

    return {
        "date": date_str,
        "one_liner": sections.get("一句话总结", "").strip(),
        "shop_sales": sections.get("店铺运营", "").strip(),
        "shop_problems": _extract_first_match(content, r"TOP\s*问题.*?\n(.+)", ""),
        "market_findings": sections.get("市场动态", "").strip(),
        "video_output": sections.get("视频产出", "").strip(),
        "cross_findings": sections.get("交叉发现", "").strip(),
        "tomorrow": sections.get("明日关注", "").strip(),
    }


def _split_sections(markdown: str) -> dict:
    """Split markdown into a dict of section-title → section-content."""
    sections = {}
    current_title = None
    current_lines = []

    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_title:
                sections[current_title] = "\n".join(current_lines)
            current_title = line[3:].strip()
            current_lines = []
        elif current_title:
            current_lines.append(line)

    if current_title:
        sections[current_title] = "\n".join(current_lines)

    return sections


def _extract_first_match(text: str, pattern: str, fallback: str) -> str:
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else fallback


def _format_text(val: str) -> str:
    """Feishu text field value: plain string (API client handles conversion)."""
    return val


def push_overview(client, data: dict) -> dict:
    """
    Push daily overview to 每日运营概览 table.
    Upsert: if a record exists for this date, update it; otherwise create.
    """
    date_str = data["date"]
    target_ts = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)

    # Read recent records and find matching date client-side
    existing = client.get(
        f"/bitable/v1/apps/{APP_TOKEN}/tables/{OVERVIEW_TABLE_ID}/records",
        params={"page_size": 10},
    )
    existing_records = existing.get("data", {}).get("items") or []
    matching = [r for r in existing_records
                if r.get("fields", {}).get("日期", 0) == target_ts]

    fields = {
        "日期": date_str,
        "一句话总结": data["one_liner"],
        "店铺销售额": data["shop_sales"],
        "店铺TOP问题": data["shop_problems"],
        "市场关键发现": data["market_findings"],
        "视频产出": data["video_output"],
        "交叉发现": data["cross_findings"],
        "明日关注": data["tomorrow"],
    }

    if matching:
        # Update existing record
        record_id = matching[0]["record_id"]
        client.put(
            f"/bitable/v1/apps/{APP_TOKEN}/tables/{OVERVIEW_TABLE_ID}/records/{record_id}",
            json_body={"fields": _to_api_fields(fields)},
        )
        print(f"📝 更新概览记录: {record_id}")
        return {"action": "updated", "record_id": record_id}
    else:
        # Create new record
        resp = client.post(
            f"/bitable/v1/apps/{APP_TOKEN}/tables/{OVERVIEW_TABLE_ID}/records",
            json_body={"fields": _to_api_fields(fields)},
        )
        record = resp.get("data", {}).get("record", {})
        record_id = record.get("record_id", "")
        print(f"✅ 创建概览记录: {record_id}")
        return {"action": "created", "record_id": record_id}


def push_actions(client, date_str: str, content: str) -> list:
    """
    Extract action items from 交叉发现 and 明日关注 sections,
    push each as a record in 每日运营追踪 table.
    """
    sections = _split_sections(content)
    cross = sections.get("交叉发现", "")
    tomorrow = sections.get("明日关注", "")

    items = []

    # Extract bullet points from cross findings
    for line in cross.splitlines():
        stripped = line.strip()
        if stripped.startswith("-") or stripped.startswith("*"):
            text = stripped.lstrip("-* ").strip()
            if text and len(text) > 5:
                items.append(("协同发现", text))

    # Extract bullet points from tomorrow
    for line in tomorrow.splitlines():
        stripped = line.strip()
        if stripped.startswith("-") or stripped.startswith("*"):
            text = stripped.lstrip("-* ").strip()
            if text and len(text) > 5:
                items.append(("行动项", text))

    if not items:
        print("ℹ️  无协同动作/行动项需要推送")
        return []

    added = 0
    for item_type, text in items:
        try:
            client.post(
                f"/bitable/v1/apps/{APP_TOKEN}/tables/{TRACKING_TABLE_ID}/records",
                json_body={
                    "fields": _to_api_fields(
                        {
                            "日期": date_str,
                            "来源Agent": "orchestrator-agent",
                            "类型": "协同发现" if item_type == "协同发现" else "行动项",
                            "摘要": text[:200],
                            "详情": text,
                            "状态": "待处理",
                            "优先级": "P1-重要",
                        }
                    )
                },
            )
            added += 1
        except FeishuAPIError as e:
            print(f"  ⚠️ 推送失败 [{item_type}]: {e}")

    print(f"📋 推送追踪记录: {added} 条")
    return items


def _to_api_fields(fields: dict) -> dict:
    """Convert plain values to Feishu API field format."""
    api_fields = {}
    for key, value in fields.items():
        if value is None or value == "":
            continue
        if isinstance(value, str):
            if key == "日期":
                # Date fields need millisecond timestamp
                try:
                    parsed = datetime.strptime(value, "%Y-%m-%d")
                    api_fields[key] = int(parsed.timestamp() * 1000)
                except ValueError:
                    api_fields[key] = value
            else:
                api_fields[key] = value
        else:
            api_fields[key] = value
    return api_fields


def main():
    # Parse date argument
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"🚀 飞书同步: {date_str}")
    print(f"   Base: {APP_TOKEN}")
    print(f"   概览表: {OVERVIEW_TABLE_ID}")
    print(f"   追踪表: {TRACKING_TABLE_ID}")

    # Validate date format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"❌ 日期格式错误: {date_str} (应为 YYYY-MM-DD)")
        sys.exit(1)

    # Parse the daily summary
    data = parse_daily_summary(date_str)
    print(f"\n📊 解析日报:")
    print(f"   一句话: {data['one_liner'][:80]}...")
    print(f"   交叉发现: {len(data['cross_findings'])} 字符")
    print(f"   明日关注: {len(data['tomorrow'])} 字符")

    # Connect to Feishu
    try:
        client = get_client()
    except Exception as e:
        print(f"❌ 飞书客户端初始化失败: {e}")
        sys.exit(1)

    # Push overview
    print(f"\n--- 概览表 ---")
    try:
        result = push_overview(client, data)
    except FeishuAPIError as e:
        print(f"❌ 推送概览失败: {e}")
        sys.exit(1)

    # Push action items
    print(f"\n--- 追踪表 ---")
    content = (OUTPUT_DIR / f"{date_str}-summary.md").read_text(encoding="utf-8")
    push_actions(client, date_str, content)

    # Summary
    base_url = f"https://vcnyjz2su8ck.feishu.cn/base/{APP_TOKEN}"
    print(f"\n✨ 同步完成!")
    print(f"   概览: {base_url}/table/{OVERVIEW_TABLE_ID}")
    print(f"   追踪: {base_url}/table/{TRACKING_TABLE_ID}")


if __name__ == "__main__":
    main()
