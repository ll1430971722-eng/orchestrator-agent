"""飞书知识库工具 — 搜索、列出空间、列出节点"""

from feishu_client import get_client


def search_kb(query: str, space_ids: list = None) -> dict:
    """搜索飞书知识库"""
    client = get_client()
    body = {"query": query}
    if space_ids:
        body["space_ids"] = space_ids

    resp = client.post("/wiki/v2/search", json_body=body)
    items = resp.get("data", {}).get("items", [])

    return {
        "query": query,
        "results": [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": (item.get("snippet") or "")[:200],
                "space_id": item.get("space_id", ""),
                "node_token": item.get("node_token", ""),
                "node_type": item.get("node_type", ""),
                "updated": item.get("update_time", ""),
            }
            for item in items[:20]
        ],
        "total": len(items),
    }


def list_kb_spaces() -> dict:
    """列出所有知识空间"""
    client = get_client()
    spaces = client.paginated_get(
        "/wiki/v2/spaces",
        item_key="items",
    )

    return {
        "spaces": [
            {
                "space_id": s.get("space_id", ""),
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "node_count": s.get("node_count", 0),
            }
            for s in spaces
        ],
        "total": len(spaces),
    }


def list_kb_nodes(space_id: str, parent_node_token: str = "") -> dict:
    """列出知识空间节点"""
    client = get_client()

    params = {"page_size": 50}
    if parent_node_token:
        params["parent_node_token"] = parent_node_token

    nodes = client.paginated_get(
        f"/wiki/v2/spaces/{space_id}/nodes",
        params=params,
        item_key="items",
    )

    return {
        "space_id": space_id,
        "parent_node_token": parent_node_token or "root",
        "nodes": [
            {
                "node_token": n.get("node_token", ""),
                "title": n.get("title", ""),
                "node_type": n.get("node_type", ""),
                "has_child": n.get("has_child", False),
                "url": n.get("url", ""),
                "updated": n.get("update_time", ""),
            }
            for n in nodes
        ],
        "total": len(nodes),
    }


def get_kb_node(node_token: str) -> dict:
    """获取知识库节点详情"""
    client = get_client()
    resp = client.get(f"/wiki/v2/spaces/get_node", params={"token": node_token})
    node = resp.get("data", {}).get("node", {})

    return {
        "node_token": node.get("node_token", node_token),
        "title": node.get("title", ""),
        "node_type": node.get("node_type", ""),
        "space_id": node.get("space_id", ""),
        "url": node.get("url", ""),
        "has_child": node.get("has_child", False),
        "updated": node.get("update_time", ""),
        "created": node.get("create_time", ""),
    }
