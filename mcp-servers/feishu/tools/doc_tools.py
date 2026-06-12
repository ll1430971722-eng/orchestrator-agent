"""飞书文档工具 — 创建、读取、追加、搜索、删除文档"""

from feishu_client import get_client, FeishuAPIError


def create_doc(title: str, content: str = "", folder_token: str = "") -> dict:
    """创建飞书文档，返回文档 ID 和 URL"""
    client = get_client()
    body = {"title": title}
    if folder_token:
        body["folder_token"] = folder_token
    resp = client.post("/docx/v1/documents", json_body=body)
    doc = resp.get("data", {}).get("document", {})
    doc_id = doc.get("document_id", "")

    # 如果有初始内容，追加
    if content and doc_id:
        blocks = _md_to_blocks(content)
        if blocks:
            try:
                client.post(
                    f"/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
                    json_body={"children": blocks},
                )
            except FeishuAPIError:
                pass  # 内容追加失败不影响创建本身

    doc_url = f"https://{_tenant_domain()}.feishu.cn/docx/{doc_id}"
    return {
        "document_id": doc_id,
        "url": doc_url,
        "title": title,
        "revision": doc.get("revision", 0),
    }


def read_doc(document_id: str) -> dict:
    """读取飞书文档内容，返回 markdown 文本"""
    client = get_client()

    # 获取文档信息
    info = client.get(f"/docx/v1/documents/{document_id}")
    doc = info.get("data", {}).get("document", {})
    title = doc.get("title", "")

    # 获取所有 blocks
    blocks = client.paginated_get(
        f"/docx/v1/documents/{document_id}/blocks",
        item_key="items",
    )

    markdown = _blocks_to_markdown(title, blocks)

    return {
        "document_id": document_id,
        "title": title,
        "content": markdown,
        "block_count": len(blocks),
        "url": f"https://{_tenant_domain()}.feishu.cn/docx/{document_id}",
    }


def append_doc(document_id: str, content: str) -> dict:
    """向飞书文档追加内容"""
    client = get_client()
    blocks = _md_to_blocks(content)
    if not blocks:
        return {"document_id": document_id, "appended_blocks": 0, "message": "无有效内容"}

    client.post(
        f"/docx/v1/documents/{document_id}/blocks/{document_id}/children",
        json_body={"children": blocks},
    )

    return {
        "document_id": document_id,
        "appended_blocks": len(blocks),
        "url": f"https://{_tenant_domain()}.feishu.cn/docx/{document_id}",
    }


def search_docs(query: str, count: int = 20) -> dict:
    """搜索飞书文档（通过云空间搜索）"""
    client = get_client()
    resp = client.post(
        "/drive/v1/files/search",
        json_body={
            "search_key": query,
            "file_types": ["docx", "doc"],
            "count": min(count, 50),
        },
    )
    files = resp.get("data", {}).get("files", [])
    return {
        "query": query,
        "results": [
            {
                "name": f.get("name", ""),
                "token": f.get("token", ""),
                "url": f.get("url", ""),
                "type": f.get("type", ""),
                "owner": f.get("owner_name", ""),
                "modified": f.get("modified_time", ""),
            }
            for f in files
        ],
        "total": len(files),
    }


def list_docs(folder_token: str = "", count: int = 50) -> dict:
    """列出文件夹下的文档"""
    client = get_client()
    body = {"page_size": min(count, 200), "file_types": ["docx", "doc", "folder"]}
    if folder_token:
        body["folder_token"] = folder_token

    resp = client.post("/drive/v1/files", json_body=body)
    files = resp.get("data", {}).get("files", [])
    return {
        "folder_token": folder_token or "root",
        "files": [
            {
                "name": f.get("name", ""),
                "token": f.get("token", ""),
                "url": f.get("url", ""),
                "type": f.get("type", ""),
                "modified": f.get("modified_time", ""),
            }
            for f in files
        ],
        "total": len(files),
        "has_more": resp.get("data", {}).get("has_more", False),
    }


def delete_doc(document_id: str) -> dict:
    """删除飞书文档（危险操作）"""
    client = get_client()
    client.delete(f"/docx/v1/documents/{document_id}")
    return {"document_id": document_id, "deleted": True}


# ---- Helpers ----

def _tenant_domain() -> str:
    import os
    app_id = os.getenv("FEISHU_APP_ID", "")
    # 尝试从 app_id 提取租户标识，或使用默认值
    return "bytedance"  # 默认域名后缀


def _blocks_to_markdown(title: str, blocks: list) -> str:
    """将飞书 blocks 转为 markdown"""
    lines = [f"# {title}\n"] if title else []
    for block in blocks:
        bt = block.get("block_type", "")
        text = _extract_block_text(block, bt)
        if not text:
            continue
        if bt in (f"heading{i}" for i in range(1, 10)):
            level = bt.replace("heading", "")
            lines.append(f"{'#' * int(level)} {text}")
        elif bt == "bullet":
            lines.append(f"- {text}")
        elif bt == "ordered":
            lines.append(f"1. {text}")
        elif bt == "code":
            lines.append(f"```\n{text}\n```")
        elif bt == "quote":
            lines.append(f"> {text}")
        elif bt == "divider":
            lines.append("---")
        else:
            lines.append(text)
        lines.append("")
    return "\n".join(lines)


def _extract_block_text(block: dict, block_type: str) -> str:
    """从 block 中提取文本"""
    content = block.get(block_type, {})
    elements = content.get("elements", [])
    parts = []
    for elem in elements:
        run = elem.get("text_run", {})
        text = run.get("content", "")
        if text:
            parts.append(text)
    return "".join(parts)


def _md_to_blocks(md_content: str) -> list:
    """将简单 markdown 转为飞书 block 列表"""
    blocks = []
    for line in md_content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("---"):
            blocks.append({"block_type": "divider", "divider": {}})
        elif line.startswith("### "):
            blocks.append(_heading_block(line[4:], 3))
        elif line.startswith("## "):
            blocks.append(_heading_block(line[3:], 2))
        elif line.startswith("# "):
            blocks.append(_heading_block(line[2:], 1))
        elif line.startswith("- "):
            blocks.append(_bullet_block(line[2:]))
        else:
            blocks.append(_text_block(line))
    return blocks


def _text_block(content: str) -> dict:
    return {
        "block_type": "text",
        "text": {"elements": [{"text_run": {"content": content}}]},
    }


def _heading_block(content: str, level: int) -> dict:
    bt = f"heading{level}"
    return {
        "block_type": bt,
        bt: {"elements": [{"text_run": {"content": content}}]},
    }


def _bullet_block(content: str) -> dict:
    return {
        "block_type": "bullet",
        "bullet": {"elements": [{"text_run": {"content": content}}]},
    }
