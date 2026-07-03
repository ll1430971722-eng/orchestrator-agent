"""飞书多维表格工具 — 列表、字段、记录读写、视图管理、仪表盘"""

import json
from feishu_client import get_client


def list_bitables(app_token: str) -> dict:
    """列出 Base 下的所有数据表"""
    client = get_client()
    resp = client.get(f"/bitable/v1/apps/{app_token}/tables")
    items = resp.get("data", {}).get("items", [])
    return {
        "app_token": app_token,
        "tables": [
            {"name": t.get("name", ""), "table_id": t.get("table_id", ""),
             "revision": t.get("revision", 0)}
            for t in items
        ],
        "total": len(items),
    }


def list_bitable_fields(app_token: str, table_id: str) -> dict:
    """列出数据表的所有字段"""
    client = get_client()
    fields = client.paginated_get(
        f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
        item_key="items",
    )
    return {
        "app_token": app_token,
        "table_id": table_id,
        "fields": [
            {
                "field_name": f.get("field_name", ""),
                "field_id": f.get("field_id", ""),
                "type": f.get("type", 0),
                "type_name": _field_type_name(f.get("type", 0)),
                "is_primary": f.get("is_primary", False),
            }
            for f in fields
        ],
        "total": len(fields),
    }


def read_bitable(
    app_token: str, table_id: str,
    filter_str: str = "", sort_str: str = "",
    max_records: int = 500,
) -> dict:
    """读取数据表记录（支持过滤和排序）"""
    client = get_client()
    records = client.paginated_get(
        f"/bitable/v1/apps/{app_token}/tables/{table_id}/records",
        item_key="items",
        max_pages=max(max_records // 500 + 1, 1),
    )

    # 展平记录
    flat_records = [_flatten_record(r) for r in records]

    # 简易客户端过滤
    if filter_str:
        flat_records = _client_filter(flat_records, filter_str)

    if len(flat_records) > max_records:
        flat_records = flat_records[:max_records]

    return {
        "app_token": app_token,
        "table_id": table_id,
        "records": flat_records,
        "total": len(flat_records),
    }


def add_bitable_records(app_token: str, table_id: str, records: list) -> dict:
    """向数据表添加记录"""
    client = get_client()

    formatted = []
    for record in records:
        fields = {}
        for key, value in record.items():
            if isinstance(value, str):
                fields[key] = [{"text": value, "type": "text"}]
            elif isinstance(value, (int, float)):
                fields[key] = value
            elif isinstance(value, list):
                fields[key] = value
            elif isinstance(value, bool):
                fields[key] = value
            elif value is None:
                continue
            else:
                fields[key] = str(value)
        formatted.append({"fields": fields})

    if not formatted:
        return {"added": 0}

    resp = client.post(
        f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
        json_body={"records": formatted},
    )
    added = resp.get("data", {}).get("records", [])
    return {
        "app_token": app_token,
        "table_id": table_id,
        "added_count": len(added),
        "record_ids": [r.get("record_id", "") for r in added],
    }


def update_bitable_records(app_token: str, table_id: str, records: list) -> dict:
    """更新数据表记录（需要提供 record_id）"""
    client = get_client()

    formatted = []
    for record in records:
        record_id = record.pop("_record_id", record.pop("record_id", None))
        if not record_id:
            continue
        fields = {}
        for key, value in record.items():
            if isinstance(value, str):
                fields[key] = [{"text": value, "type": "text"}]
            elif isinstance(value, (int, float, bool, list)):
                fields[key] = value
            elif value is None:
                continue
            else:
                fields[key] = str(value)
        formatted.append({"record_id": record_id, "fields": fields})

    if not formatted:
        return {"updated": 0}

    resp = client.post(
        f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update",
        json_body={"records": formatted},
    )
    updated = resp.get("data", {}).get("records", [])
    return {
        "app_token": app_token,
        "table_id": table_id,
        "updated_count": len(updated),
    }


def create_bitable_table(app_token: str, name: str, fields: list = None) -> dict:
    """创建新数据表"""
    client = get_client()

    default_fields = fields or [
        {"field_name": "名称", "type": 1},
        {"field_name": "备注", "type": 1},
    ]

    resp = client.post(
        f"/bitable/v1/apps/{app_token}/tables",
        json_body={
            "table": {
                "name": name,
                "fields": default_fields,
            }
        },
    )
    table = resp.get("data", {}).get("table", {}) or resp.get("data", {})
    return {
        "app_token": app_token,
        "table_id": table.get("table_id", ""),
        "name": table.get("name", name),
        "url": f"https://{_tenant_domain()}.feishu.cn/base/{app_token}/table/{table.get('table_id', '')}",
    }


# ---- Helpers ----

_FIELD_TYPES = {
    1: "text", 2: "number", 3: "single_select", 4: "multi_select",
    5: "datetime", 7: "checkbox", 11: "url", 13: "attachment",
    15: "formula", 17: "lookup", 18: "created_time", 19: "modified_time",
    20: "created_by", 21: "modified_by", 22: "auto_number",
    23: "duplex_link", 24: "location", 1001: "currency", 1002: "progress",
    1003: "rating", 1004: "phone", 1005: "email",
}


def _field_type_name(type_num: int) -> str:
    return _FIELD_TYPES.get(type_num, f"unknown({type_num})")


def _flatten_record(record: dict) -> dict:
    row = {"_record_id": record.get("record_id", "")}
    for fn, val in record.get("fields", {}).items():
        if isinstance(val, list) and len(val) > 0:
            item = val[0]
            row[fn] = item.get("text", str(item)) if isinstance(item, dict) else item
        else:
            row[fn] = val
    return row


def _client_filter(records: list, filter_str: str) -> list:
    """简易客户端过滤: field_name=value 或 field_name contains value"""
    if "=" in filter_str:
        key, val = filter_str.split("=", 1)
        key, val = key.strip(), val.strip()
        return [r for r in records if str(r.get(key, "")) == val]
    if " contains " in filter_str:
        key, val = filter_str.split(" contains ", 1)
        key, val = key.strip(), val.strip()
        return [r for r in records if val.lower() in str(r.get(key, "")).lower()]
    return records


def _tenant_domain() -> str:
    import os
    return os.getenv("FEISHU_TENANT_DOMAIN", "")


# ═══════════════════════════════════════════════════════
# 视图管理（Step 2: 4 tools）
# ═══════════════════════════════════════════════════════

def list_bitable_views(app_token: str, table_id: str) -> dict:
    """列出数据表的所有视图"""
    client = get_client()
    resp = client.get(
        f"/bitable/v1/apps/{app_token}/tables/{table_id}/views",
        params={"page_size": 200},
    )
    items = resp.get("data", {}).get("items", [])
    return {
        "app_token": app_token,
        "table_id": table_id,
        "views": [
            {
                "view_id": v.get("view_id", ""),
                "view_name": v.get("view_name", ""),
                "view_type": v.get("view_type", "grid"),
            }
            for v in items
        ],
        "total": len(items),
    }


def create_bitable_view(
    app_token: str, table_id: str,
    view_name: str, view_type: str = "grid",
) -> dict:
    """创建新视图（grid/kanban/gantt/gallery/form）"""
    client = get_client()

    valid_types = {"grid", "kanban", "gantt", "gallery", "form"}
    if view_type not in valid_types:
        view_type = "grid"

    resp = client.post(
        f"/bitable/v1/apps/{app_token}/tables/{table_id}/views",
        json_body={
            "view_name": view_name,
            "view_type": view_type,
        },
    )
    view = resp.get("data", {}).get("view", {})
    return {
        "app_token": app_token,
        "table_id": table_id,
        "view_id": view.get("view_id", ""),
        "view_name": view.get("view_name", view_name),
        "view_type": view.get("view_type", view_type),
        "url": f"https://{_tenant_domain()}.feishu.cn/base/{app_token}/table/{table_id}?view={view.get('view_id', '')}",
    }


def update_bitable_view(
    app_token: str, table_id: str, view_id: str,
    property_updates: dict = None,
) -> dict:
    """更新视图属性（筛选、排序、显示字段等）"""
    client = get_client()

    body = {}
    if property_updates:
        body["property"] = property_updates

    resp = client.patch(
        f"/bitable/v1/apps/{app_token}/tables/{table_id}/views/{view_id}",
        json_body=body,
    )
    view = resp.get("data", {}).get("view", {})
    return {
        "app_token": app_token,
        "table_id": table_id,
        "view_id": view_id,
        "view_name": view.get("view_name", ""),
        "updated": True,
    }


def delete_bitable_view(
    app_token: str, table_id: str, view_id: str,
) -> dict:
    """删除指定视图"""
    client = get_client()
    client.delete(
        f"/bitable/v1/apps/{app_token}/tables/{table_id}/views/{view_id}"
    )
    return {
        "app_token": app_token,
        "table_id": table_id,
        "view_id": view_id,
        "deleted": True,
    }


# ═══════════════════════════════════════════════════════
# 字段管理（Step 3: 3 tools）
# ═══════════════════════════════════════════════════════

def add_bitable_fields(
    app_token: str, table_id: str, fields: list,
) -> dict:
    """向已有数据表新增字段

    fields 每项示例:
      - 文本: {"field_name": "备注", "type": 1}
      - 数字: {"field_name": "数量", "type": 2}
      - 货币: {"field_name": "金额", "type": 2, "ui_type": "Currency", "property": {"decimal_places": 2}}
      - 进度: {"field_name": "完成率", "type": 2, "ui_type": "Progress", "property": {"range": {"min": 0, "max": 1}}}
      - 评分: {"field_name": "评分", "type": 2, "ui_type": "Rating", "property": {"rating": {"max": 5, "icon": "star"}}}
      - 单选: {"field_name": "状态", "type": 3, "property": {"options": [{"name": "待处理", "color": 1}]}}
      - 公式: {"field_name": "合计", "type": 20, "property": {"formula_expression": "[A] + [B]"}}
      - 日期: {"field_name": "日期", "type": 5, "property": {"format": "yyyy-mm-dd"}}
    """
    client = get_client()

    added = []
    errors = []
    for fdef in fields:
        try:
            resp = client.post(
                f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                json_body=fdef,
            )
            field = resp.get("data", {}).get("field", {})
            added.append({
                "field_name": field.get("field_name", fdef.get("field_name", "")),
                "field_id": field.get("field_id", ""),
                "type": field.get("type", 0),
            })
        except Exception as e:
            errors.append({
                "field_name": fdef.get("field_name", "unknown"),
                "error": str(e),
            })

    return {
        "app_token": app_token,
        "table_id": table_id,
        "added_fields": added,
        "added_count": len(added),
        "errors": errors,
    }


def update_bitable_fields(
    app_token: str, table_id: str, field_updates: list,
) -> dict:
    """更新已有字段属性（改名称、类型、ui_type、选项等）

    field_updates 每项必须包含 field_id，其余字段为要更新的内容:
      {"field_id": "fldxxx", "field_name": "新名称", "type": 2, "ui_type": "Currency"}
      注意: 更新单选字段时需传完整 options 列表（会覆盖原有选项）
    """
    client = get_client()

    updated = []
    errors = []
    for upd in field_updates:
        field_id = upd.pop("field_id", None)
        if not field_id:
            errors.append({"error": "缺少 field_id"})
            continue
        try:
            resp = client.put(
                f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}",
                json_body=upd,
            )
            field = resp.get("data", {}).get("field", {})
            updated.append({
                "field_name": field.get("field_name", upd.get("field_name", "")),
                "field_id": field_id,
            })
        except Exception as e:
            errors.append({
                "field_id": field_id,
                "error": str(e),
            })

    return {
        "app_token": app_token,
        "table_id": table_id,
        "updated_fields": updated,
        "updated_count": len(updated),
        "errors": errors,
    }


def delete_bitable_fields(
    app_token: str, table_id: str, field_ids: list,
) -> dict:
    """删除指定字段（⚠️ 不可恢复，数据会被删除）"""
    client = get_client()

    deleted = []
    errors = []
    for fid in field_ids:
        try:
            client.delete(
                f"/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{fid}"
            )
            deleted.append(fid)
        except Exception as e:
            errors.append({"field_id": fid, "error": str(e)})

    return {
        "app_token": app_token,
        "table_id": table_id,
        "deleted_ids": deleted,
        "deleted_count": len(deleted),
        "errors": errors,
    }


# ═══════════════════════════════════════════════════════
# 记录删除（Step 4a: 2 tools）
# ═══════════════════════════════════════════════════════

def delete_bitable_records(
    app_token: str, table_id: str, record_ids: list,
) -> dict:
    """删除数据表记录（支持批量，最多500条/次）

    传入 record_id 列表，批量删除。适合清理旧数据或错误数据。
    """
    client = get_client()

    if not record_ids:
        return {"deleted_count": 0, "record_ids": []}

    # 分批，每批最多 500 条
    deleted_ids = []
    errors = []
    batch_size = 500

    for i in range(0, len(record_ids), batch_size):
        batch = record_ids[i:i + batch_size]
        try:
            client.post(
                f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete",
                json_body={"records": batch},
            )
            deleted_ids.extend(batch)
        except Exception as e:
            # 批量删除失败时，逐条重试
            for rid in batch:
                try:
                    client.delete(
                        f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{rid}"
                    )
                    deleted_ids.append(rid)
                except Exception as e2:
                    errors.append({"record_id": rid, "error": str(e2)})

    return {
        "app_token": app_token,
        "table_id": table_id,
        "deleted_count": len(deleted_ids),
        "record_ids": deleted_ids,
        "errors": errors,
    }


# ═══════════════════════════════════════════════════════
# 仪表盘（Step 4b: 2 tools）
# ═══════════════════════════════════════════════════════

def list_bitable_dashboards(app_token: str) -> dict:
    """列出多维表格 Base 下的所有仪表盘"""
    client = get_client()
    resp = client.get(
        f"/bitable/v1/apps/{app_token}/dashboards",
        params={"page_size": 100},
    )
    items = resp.get("data", {}).get("dashboards", [])
    return {
        "app_token": app_token,
        "dashboards": [
            {
                "block_id": d.get("block_id", ""),
                "name": d.get("name", ""),
            }
            for d in items
        ],
        "total": len(items),
    }


def copy_bitable_dashboard(
    app_token: str, block_id: str, name: str,
) -> dict:
    """复制仪表盘（用于从模板批量创建）

    由于飞书 API 不支持直接创建空白仪表盘，
    需要先在 UI 中手动创建一个模板仪表盘，然后通过此工具复制。
    """
    client = get_client()
    resp = client.post(
        f"/bitable/v1/apps/{app_token}/dashboards/{block_id}/copy",
        json_body={"name": name},
    )
    dashboard = resp.get("data", {}).get("dashboard", {}) or resp.get("data", {})
    return {
        "app_token": app_token,
        "block_id": dashboard.get("block_id", ""),
        "name": dashboard.get("name", name),
        "url": f"https://{_tenant_domain()}.feishu.cn/base/{app_token}/{dashboard.get('block_id', '')}",
    }
