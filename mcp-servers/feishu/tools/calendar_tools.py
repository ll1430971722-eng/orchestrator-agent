"""飞书日历工具 — 列出日历、日程，创建日程"""

from feishu_client import get_client


def list_calendars() -> dict:
    """列出当前用户的所有日历"""
    client = get_client()
    resp = client.get("/calendar/v4/calendars")
    items = resp.get("data", {}).get("calendar_list", [])
    return {
        "calendars": [
            {
                "calendar_id": c.get("calendar_id", ""),
                "summary": c.get("summary", ""),
                "description": c.get("description", ""),
                "type": c.get("type", ""),
            }
            for c in items
        ],
        "total": len(items),
    }


def list_events(
    calendar_id: str,
    start_time: str = "",
    end_time: str = "",
    page_size: int = 50,
) -> dict:
    """列出日历中的日程

    start_time/end_time 格式: "2026-06-09T00:00:00+08:00" 或 Unix timestamp
    """
    client = get_client()
    params = {"page_size": min(page_size, 100)}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time

    resp = client.get(
        f"/calendar/v4/calendars/{calendar_id}/events",
        params=params,
    )
    items = resp.get("data", {}).get("items", [])

    return {
        "calendar_id": calendar_id,
        "events": [
            {
                "event_id": e.get("event_id", ""),
                "summary": e.get("summary", ""),
                "description": e.get("description", ""),
                "start_time": e.get("start_time", {}).get("timestamp", ""),
                "end_time": e.get("end_time", {}).get("timestamp", ""),
                "status": e.get("status", ""),
                "organizer": e.get("organizer", {}).get("display_name", ""),
            }
            for e in items
        ],
        "total": len(items),
        "has_more": resp.get("data", {}).get("has_more", False),
    }


def create_event(
    calendar_id: str,
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    attendees: list = None,
) -> dict:
    """创建日历日程

    start_time/end_time 示例: "1717920000" (Unix timestamp)
    """
    client = get_client()

    body = {
        "summary": summary,
        "start_time": {"timestamp": start_time},
        "end_time": {"timestamp": end_time},
    }
    if description:
        body["description"] = description
    if attendees:
        body["attendees"] = [
            {"type": a.get("type", "open_id"), "id": a.get("id", "")}
            for a in attendees
        ]

    resp = client.post(
        f"/calendar/v4/calendars/{calendar_id}/events",
        json_body=body,
    )
    event = resp.get("data", {}).get("event", {})

    return {
        "event_id": event.get("event_id", ""),
        "summary": event.get("summary", summary),
        "start_time": event.get("start_time", {}).get("timestamp", start_time),
        "end_time": event.get("end_time", {}).get("timestamp", end_time),
        "status": event.get("status", ""),
    }
