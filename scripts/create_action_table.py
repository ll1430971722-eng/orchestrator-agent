#!/usr/bin/env python3
"""创建 抖音行动建议明细 表"""
import sys
from pathlib import Path

ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent
FEISHU_MCP = ORCHESTRATOR_ROOT / "mcp-servers" / "feishu"
sys.path.insert(0, str(FEISHU_MCP))

from feishu_client import get_client

APP_TOKEN = "GPFtbIOhCafB4HsANmVcbFOan4f"

fields = [
    {"field_name": "日期", "type": 5},
    {"field_name": "关联问题", "type": 1},
    {"field_name": "优先级",
     "type": 3,
     "property": {
         "options": [
             {"name": "🔴严重", "color": 1},
             {"name": "🟡注意", "color": 2},
             {"name": "🟢观察", "color": 3},
         ]
     }},
    {"field_name": "建议动作", "type": 1},
    {"field_name": "为什么这样做", "type": 1},
    {"field_name": "状态",
     "type": 3,
     "property": {
         "options": [
             {"name": "待处理", "color": 1},
             {"name": "处理中", "color": 2},
             {"name": "已完成", "color": 3},
             {"name": "暂缓", "color": 4},
         ]
     }},
]

client = get_client()
resp = client.post(
    f"/bitable/v1/apps/{APP_TOKEN}/tables",
    json_body={"table": {"name": "抖音行动建议明细", "fields": fields}},
)
table = resp.get("data", {}).get("table", {}) or resp.get("data", {})
table_id = table.get("table_id", "")
print(f"✅ 表3创建成功: 抖音行动建议明细")
print(f"   table_id: {table_id}")
print(f"   ACTION_TABLE_ID = {table_id!r}")
