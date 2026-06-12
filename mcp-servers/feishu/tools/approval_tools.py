"""飞书审批工具 — 列出审批实例、获取审批详情"""

from feishu_client import get_client


def list_approvals(
    status: str = "PENDING",
    page_size: int = 20,
    start_time: str = "",
    end_time: str = "",
) -> dict:
    """列出审批实例

    status: PENDING / APPROVED / REJECTED / CANCELED / ALL
    """
    client = get_client()

    body = {
        "page_size": min(page_size, 50),
        "approval_status": status,
    }
    if start_time:
        body["start_time"] = start_time
    if end_time:
        body["end_time"] = end_time

    resp = client.post(
        "/approval/v4/instances",
        json_body=body,
    )
    items = resp.get("data", {}).get("instance_list", [])

    return {
        "status_filter": status,
        "approvals": [
            {
                "instance_code": i.get("instance_code", ""),
                "approval_name": i.get("approval_name", ""),
                "status": i.get("status", ""),
                "applicant": i.get("applicant_name", "") or i.get("applicant_id", ""),
                "start_time": i.get("start_time", ""),
                "end_time": i.get("end_time", ""),
                "form_url": i.get("form_url", ""),
            }
            for i in items
        ],
        "total": len(items),
        "has_more": resp.get("data", {}).get("has_more", False),
    }


def get_approval(instance_code: str) -> dict:
    """获取审批实例详情"""
    client = get_client()
    resp = client.get(
        "/approval/v4/instances",
        params={"instance_code": instance_code},
    )
    items = resp.get("data", {}).get("instance_list", [])
    if not items:
        return {"instance_code": instance_code, "error": "未找到该审批"}

    i = items[0]
    return {
        "instance_code": i.get("instance_code", ""),
        "approval_name": i.get("approval_name", ""),
        "status": i.get("status", ""),
        "applicant": i.get("applicant_name", "") or i.get("applicant_id", ""),
        "department": i.get("department_name", ""),
        "start_time": i.get("start_time", ""),
        "end_time": i.get("end_time", ""),
        "form_url": i.get("form_url", ""),
        "form_data": i.get("form", ""),
    }
