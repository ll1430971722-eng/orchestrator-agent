"""飞书消息工具 — 发送消息、列出消息"""

import json
import requests
from feishu_client import get_client


def send_message(
    receive_id: str,
    content: str,
    msg_type: str = "text",
    receive_id_type: str = "open_id",
) -> dict:
    """通过飞书应用发送消息"""
    client = get_client()

    body = {
        "receive_id": receive_id,
        "msg_type": msg_type,
        "content": json.dumps({"text": content}) if msg_type == "text" else content,
    }

    # receive_id_type 在 URL query 中
    path = f"/im/v1/messages?receive_id_type={receive_id_type}"
    resp = client.post(path, json_body=body)

    msg = resp.get("data", {})
    return {
        "message_id": msg.get("message_id", ""),
        "chat_id": msg.get("chat_id", ""),
        "sender_id": msg.get("sender", {}).get("id", ""),
        "status": "sent",
    }


def send_webhook(webhook_url: str, content: str, title: str = "") -> dict:
    """通过 Webhook 发送消息（无需应用凭证）"""
    if title:
        msg = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "blue",
                },
                "elements": [{"tag": "markdown", "content": content}],
            },
        }
    else:
        msg = {"msg_type": "text", "content": {"text": content}}

    resp = requests.post(webhook_url, json=msg, timeout=10)
    resp.raise_for_status()
    result = resp.json()

    return {
        "status": "sent",
        "code": result.get("code", -1),
        "msg": result.get("msg", ""),
    }


def list_messages(chat_id: str = "", page_size: int = 20) -> dict:
    """列出最近消息（需要 chat_id 或接收最近会话）"""
    client = get_client()

    # 如果有 chat_id，列出该会话消息
    if chat_id:
        resp = client.get(
            f"/im/v1/messages",
            params={
                "receive_id_type": "chat_id",
                "receive_id": chat_id,
                "page_size": min(page_size, 50),
                "sort_type": "ByCreateTimeDesc",
            },
        )
        items = resp.get("data", {}).get("items", [])
    else:
        # 列出最近会话列表
        resp = client.get("/im/v1/chats", params={"page_size": min(page_size, 50)})
        items = resp.get("data", {}).get("items", [])

    return {
        "messages": [
            {
                "message_id": m.get("message_id", ""),
                "chat_id": m.get("chat_id", ""),
                "msg_type": m.get("msg_type", ""),
                "content": _extract_text(m),
                "sender": m.get("sender", {}).get("id", ""),
                "create_time": m.get("create_time", ""),
            }
            for m in items
        ],
        "total": len(items),
    }


def _extract_text(message: dict) -> str:
    """从消息中提取文本内容"""
    content = message.get("body", {}).get("content", "")
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed.get("text", content)
        except json.JSONDecodeError:
            pass
    return str(content)[:500]
