"""飞书云空间工具 — 列出文件、搜索文件、获取文件信息"""

from feishu_client import get_client


def list_files(
    folder_token: str = "",
    page_size: int = 50,
    file_types: list = None,
) -> dict:
    """列出云空间文件（根目录或指定文件夹）"""
    client = get_client()

    body = {"page_size": min(page_size, 200)}
    if folder_token:
        body["folder_token"] = folder_token
    if file_types:
        body["file_types"] = file_types

    resp = client.post("/drive/v1/files", json_body=body)
    data = resp.get("data", {})
    files = data.get("files", [])

    return {
        "folder_token": folder_token or "root",
        "files": [
            {
                "name": f.get("name", ""),
                "token": f.get("token", ""),
                "url": f.get("url", ""),
                "type": f.get("type", ""),
                "size": f.get("size", 0),
                "owner": f.get("owner_name", ""),
                "modified": f.get("modified_time", ""),
                "created": f.get("created_time", ""),
            }
            for f in files
        ],
        "total": len(files),
        "has_more": data.get("has_more", False),
    }


def get_file_info(file_token: str) -> dict:
    """获取文件元信息"""
    client = get_client()
    resp = client.get(f"/drive/v1/files/{file_token}")
    f = resp.get("data", {}).get("file", resp.get("data", {}))

    return {
        "token": f.get("token", file_token),
        "name": f.get("name", ""),
        "url": f.get("url", ""),
        "type": f.get("type", ""),
        "size": f.get("size", 0),
        "owner_id": f.get("owner_id", ""),
        "owner_name": f.get("owner_name", ""),
        "modified": f.get("modified_time", ""),
        "created": f.get("created_time", ""),
        "version": f.get("version", ""),
    }


def search_files(
    query: str,
    file_types: list = None,
    count: int = 20,
) -> dict:
    """搜索云空间文件"""
    client = get_client()

    types = file_types or ["docx", "doc", "sheet", "bitable", "mindnote", "file"]
    body = {
        "search_key": query,
        "file_types": types,
        "count": min(count, 50),
    }

    resp = client.post("/drive/v1/files/search", json_body=body)
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
