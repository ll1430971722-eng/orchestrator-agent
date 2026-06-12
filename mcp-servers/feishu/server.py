"""
Feishu MCP Server — 飞书开放平台全功能 MCP Server

提供飞书文档、多维表格、消息、日历、云空间、知识库、审批的完整操作工具集。
"""

import json
import sys
import os

# 确保能从项目根目录加载 .env
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from feishu_client import FeishuAPIError, get_client

# ---- Import tool modules ----
from tools import doc_tools
from tools import bitable_tools
from tools import message_tools
from tools import calendar_tools
from tools import drive_tools
from tools import wiki_tools
from tools import approval_tools

# ---- Create MCP Server ----
server = Server("feishu-agent")


# ---- Helper to register tools ----

def _error_result(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"error": msg}, ensure_ascii=False))]


def _ok_result(data: dict) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


# ---- List Tools ----

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ---- 文档工具 ----
        Tool(
            name="feishu_create_doc",
            description="创建飞书文档。输入标题和可选的初始内容（markdown），返回文档ID和URL。",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "文档标题"},
                    "content": {"type": "string", "description": "初始内容（markdown格式，可选）"},
                    "folder_token": {"type": "string", "description": "父文件夹token（可选，不填则创建在根目录）"},
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="feishu_read_doc",
            description="读取飞书文档内容，返回markdown格式的完整内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "飞书文档ID（从文档URL中获取）"},
                },
                "required": ["document_id"],
            },
        ),
        Tool(
            name="feishu_append_doc",
            description="向飞书文档末尾追加内容（markdown格式）。⚠️ 会修改文档内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "飞书文档ID"},
                    "content": {"type": "string", "description": "要追加的内容（markdown格式）"},
                },
                "required": ["document_id", "content"],
            },
        ),
        Tool(
            name="feishu_search_docs",
            description="搜索飞书文档。按关键词在云空间中搜索。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "count": {"type": "integer", "description": "返回数量，默认20，最大50"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="feishu_list_docs",
            description="列出云空间文件夹下的文件和文档。",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_token": {"type": "string", "description": "文件夹token（不填则列出根目录）"},
                    "count": {"type": "integer", "description": "返回数量，默认50"},
                },
            },
        ),
        Tool(
            name="feishu_delete_doc",
            description="删除飞书文档。⚠️ 危险操作，不可恢复！",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "要删除的文档ID"},
                },
                "required": ["document_id"],
            },
        ),

        # ---- 多维表格工具 ----
        Tool(
            name="feishu_list_bitables",
            description="列出飞书多维表格Base下的所有数据表。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token（从URL获取）"},
                },
                "required": ["app_token"],
            },
        ),
        Tool(
            name="feishu_list_bitable_fields",
            description="列出多维表格数据表的所有字段（列定义）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                },
                "required": ["app_token", "table_id"],
            },
        ),
        Tool(
            name="feishu_read_bitable",
            description="读取多维表格的数据记录。可指定过滤条件和最大记录数。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                    "filter": {"type": "string", "description": "过滤条件，如 'status=待处理' 或 'name contains 笔袋'（可选）"},
                    "max_records": {"type": "integer", "description": "最大返回记录数，默认500"},
                },
                "required": ["app_token", "table_id"],
            },
        ),
        Tool(
            name="feishu_add_bitable_records",
            description="向多维表格数据表添加记录。⚠️ 会修改表格内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                    "records": {
                        "type": "array",
                        "description": "要添加的记录列表，每项为 {字段名: 值} 的字典",
                        "items": {"type": "object"},
                    },
                },
                "required": ["app_token", "table_id", "records"],
            },
        ),
        Tool(
            name="feishu_update_bitable_records",
            description="更新多维表格的记录。⚠️ 会修改表格内容。每条记录需包含 _record_id。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                    "records": {
                        "type": "array",
                        "description": "要更新的记录列表，每项需包含 _record_id 和要修改的字段",
                        "items": {"type": "object"},
                    },
                },
                "required": ["app_token", "table_id", "records"],
            },
        ),
        Tool(
            name="feishu_create_bitable_table",
            description="在多维表格Base中创建新数据表。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "name": {"type": "string", "description": "新数据表名称"},
                    "fields": {"type": "array", "description": "字段定义列表（可选，默认创建'名称'+'备注'字段）", "items": {"type": "object"}},
                },
                "required": ["app_token", "name"],
            },
        ),

        # ---- 视图管理工具 ----
        Tool(
            name="feishu_list_bitable_views",
            description="列出多维表格数据表的所有视图（表格、看板、甘特、画册、表单）。返回视图ID、名称和类型。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                },
                "required": ["app_token", "table_id"],
            },
        ),
        Tool(
            name="feishu_create_bitable_view",
            description="在数据表中创建新视图。支持表格(grid)、看板(kanban)、甘特(gantt)、画册(gallery)、表单(form)五种视图类型。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                    "view_name": {"type": "string", "description": "视图名称，如'老板看板'、'运营数据全览'、'渠道分析'"},
                    "view_type": {"type": "string", "description": "视图类型：grid（表格）/kanban（看板）/gantt（甘特）/gallery（画册）/form（表单），默认grid"},
                },
                "required": ["app_token", "table_id", "view_name"],
            },
        ),
        Tool(
            name="feishu_update_bitable_view",
            description="更新视图属性，可设置筛选条件、排序规则、显示字段、分组方式等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                    "view_id": {"type": "string", "description": "视图ID（从feishu_list_bitable_views获取）"},
                    "property": {"type": "object", "description": "视图属性：{filter_info: 筛选条件, sort_info: 排序规则, display_fields: 显示字段列表, grid_config: 表格配置(冻结列等)}"},
                },
                "required": ["app_token", "table_id", "view_id"],
            },
        ),
        Tool(
            name="feishu_delete_bitable_view",
            description="删除数据表的指定视图。⚠️ 删除后不可恢复！",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                    "view_id": {"type": "string", "description": "要删除的视图ID"},
                },
                "required": ["app_token", "table_id", "view_id"],
            },
        ),

        # ---- 字段管理工具 ----
        Tool(
            name="feishu_add_bitable_fields",
            description="向已有数据表新增字段。支持所有字段类型：文本(1)、数字(2)、单选(3)、多选(4)、日期(5)、复选框(7)、超链接(15)、附件(17)、公式(20)等。数字字段可设置ui_type为Currency(货币)/Progress(进度条)/Rating(评分)。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                    "fields": {
                        "type": "array",
                        "description": "字段定义列表。每项含field_name(必填), type(必填), ui_type(可选), property(可选)",
                        "items": {"type": "object"},
                    },
                },
                "required": ["app_token", "table_id", "fields"],
            },
        ),
        Tool(
            name="feishu_update_bitable_fields",
            description="更新已有字段属性：修改字段名、类型、ui_type（如数字改为货币/进度条/评分）、选项（单选/多选的选项列表）等。更新单选字段时需传完整的options列表（会覆盖原有选项）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                    "field_updates": {
                        "type": "array",
                        "description": "字段更新列表。每项必须包含 field_id，其余为要更新的属性",
                        "items": {"type": "object"},
                    },
                },
                "required": ["app_token", "table_id", "field_updates"],
            },
        ),
        Tool(
            name="feishu_delete_bitable_fields",
            description="删除指定字段。⚠️ 危险操作：字段和对应数据会永久删除，不可恢复！",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                    "field_ids": {
                        "type": "array",
                        "description": "要删除的字段ID列表",
                        "items": {"type": "string"},
                    },
                },
                "required": ["app_token", "table_id", "field_ids"],
            },
        ),

        # ---- 记录删除工具 ----
        Tool(
            name="feishu_delete_bitable_records",
            description="删除数据表记录（支持批量）。传入record_id列表，自动分批（每批≤500条）。适合清理旧数据或错误数据。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "table_id": {"type": "string", "description": "数据表ID"},
                    "record_ids": {
                        "type": "array",
                        "description": "要删除的记录ID列表",
                        "items": {"type": "string"},
                    },
                },
                "required": ["app_token", "table_id", "record_ids"],
            },
        ),

        # ---- 仪表盘工具 ----
        Tool(
            name="feishu_list_bitable_dashboards",
            description="列出多维表格Base下的所有仪表盘（Dashboard）。返回仪表盘的block_id和名称。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                },
                "required": ["app_token"],
            },
        ),
        Tool(
            name="feishu_copy_bitable_dashboard",
            description="复制仪表盘（从模板批量创建）。飞书API不支持直接创建空白仪表盘，需先在UI中手动创建一个模板，再用此工具复制。",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_token": {"type": "string", "description": "多维表格App Token"},
                    "block_id": {"type": "string", "description": "源仪表盘的block_id（从feishu_list_bitable_dashboards获取）"},
                    "name": {"type": "string", "description": "新仪表盘名称"},
                },
                "required": ["app_token", "block_id", "name"],
            },
        ),

        # ---- 消息工具 ----
        Tool(
            name="feishu_send_message",
            description="通过飞书应用发送消息给用户或群聊。",
            inputSchema={
                "type": "object",
                "properties": {
                    "receive_id": {"type": "string", "description": "接收者ID（open_id 或 chat_id）"},
                    "content": {"type": "string", "description": "消息内容"},
                    "msg_type": {"type": "string", "description": "消息类型（text/interactive），默认text"},
                    "receive_id_type": {"type": "string", "description": "接收者ID类型（open_id/chat_id/user_id/email），默认open_id"},
                },
                "required": ["receive_id", "content"],
            },
        ),
        Tool(
            name="feishu_send_webhook",
            description="通过群机器人Webhook发送消息（最简单方式，无需复杂权限）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "webhook_url": {"type": "string", "description": "群机器人Webhook URL"},
                    "content": {"type": "string", "description": "消息内容（markdown格式）"},
                    "title": {"type": "string", "description": "卡片标题（可选，有标题时发送富文本卡片）"},
                },
                "required": ["webhook_url", "content"],
            },
        ),
        Tool(
            name="feishu_list_messages",
            description="列出飞书会话的最近消息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string", "description": "群聊ID（不填则列出最近会话列表）"},
                    "page_size": {"type": "integer", "description": "返回数量，默认20"},
                },
            },
        ),

        # ---- 日历工具 ----
        Tool(
            name="feishu_list_calendars",
            description="列出飞书日历列表。",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="feishu_list_events",
            description="列出飞书日历中的日程。",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "日历ID"},
                    "start_time": {"type": "string", "description": "开始时间，如 '2026-06-09T00:00:00+08:00'"},
                    "end_time": {"type": "string", "description": "结束时间"},
                    "page_size": {"type": "integer", "description": "返回数量，默认50"},
                },
                "required": ["calendar_id"],
            },
        ),
        Tool(
            name="feishu_create_event",
            description="创建飞书日历日程。",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_id": {"type": "string", "description": "日历ID"},
                    "summary": {"type": "string", "description": "日程标题"},
                    "start_time": {"type": "string", "description": "开始时间（Unix timestamp字符串）"},
                    "end_time": {"type": "string", "description": "结束时间（Unix timestamp字符串）"},
                    "description": {"type": "string", "description": "日程描述（可选）"},
                    "attendees": {
                        "type": "array",
                        "description": "参与者列表（可选），每项为 {type: 'open_id', id: 'xxx'}",
                        "items": {"type": "object"},
                    },
                },
                "required": ["calendar_id", "summary", "start_time", "end_time"],
            },
        ),

        # ---- 云空间工具 ----
        Tool(
            name="feishu_list_files",
            description="列出飞书云空间文件和文件夹。",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_token": {"type": "string", "description": "文件夹token（不填则列出根目录）"},
                    "page_size": {"type": "integer", "description": "返回数量，默认50"},
                    "file_types": {"type": "array", "description": "文件类型过滤，如 ['docx', 'sheet']", "items": {"type": "string"}},
                },
            },
        ),
        Tool(
            name="feishu_get_file_info",
            description="获取飞书文件/文件夹的详细信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_token": {"type": "string", "description": "文件token"},
                },
                "required": ["file_token"],
            },
        ),
        Tool(
            name="feishu_search_files",
            description="在飞书云空间中搜索文件。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "file_types": {"type": "array", "description": "文件类型过滤", "items": {"type": "string"}},
                    "count": {"type": "integer", "description": "返回数量，默认20"},
                },
                "required": ["query"],
            },
        ),

        # ---- 知识库工具 ----
        Tool(
            name="feishu_search_kb",
            description="搜索飞书知识库内容。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "space_ids": {"type": "array", "description": "限定知识空间ID列表（可选）", "items": {"type": "string"}},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="feishu_list_kb_spaces",
            description="列出所有飞书知识空间。",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="feishu_list_kb_nodes",
            description="列出知识空间下的节点（文档/文件夹）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "space_id": {"type": "string", "description": "知识空间ID"},
                    "parent_node_token": {"type": "string", "description": "父节点token（不填则列出根节点）"},
                },
                "required": ["space_id"],
            },
        ),
        Tool(
            name="feishu_get_kb_node",
            description="获取知识库节点详情。",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_token": {"type": "string", "description": "节点token"},
                },
                "required": ["node_token"],
            },
        ),

        # ---- 审批工具 ----
        Tool(
            name="feishu_list_approvals",
            description="列出飞书审批实例。",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "审批状态：PENDING/APPROVED/REJECTED/CANCELED/ALL，默认PENDING"},
                    "page_size": {"type": "integer", "description": "返回数量，默认20"},
                    "start_time": {"type": "string", "description": "开始时间（Unix timestamp）"},
                    "end_time": {"type": "string", "description": "结束时间（Unix timestamp）"},
                },
            },
        ),
        Tool(
            name="feishu_get_approval",
            description="获取飞书审批实例详情。",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_code": {"type": "string", "description": "审批实例代码"},
                },
                "required": ["instance_code"],
            },
        ),
    ]


# ---- Call Tool ----

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        # ---- 文档 ----
        if name == "feishu_create_doc":
            result = doc_tools.create_doc(
                title=arguments["title"],
                content=arguments.get("content", ""),
                folder_token=arguments.get("folder_token", ""),
            )
            return _ok_result(result)

        elif name == "feishu_read_doc":
            result = doc_tools.read_doc(arguments["document_id"])
            return _ok_result(result)

        elif name == "feishu_append_doc":
            result = doc_tools.append_doc(
                arguments["document_id"],
                arguments["content"],
            )
            return _ok_result(result)

        elif name == "feishu_search_docs":
            result = doc_tools.search_docs(
                query=arguments["query"],
                count=arguments.get("count", 20),
            )
            return _ok_result(result)

        elif name == "feishu_list_docs":
            result = doc_tools.list_docs(
                folder_token=arguments.get("folder_token", ""),
                count=arguments.get("count", 50),
            )
            return _ok_result(result)

        elif name == "feishu_delete_doc":
            result = doc_tools.delete_doc(arguments["document_id"])
            return _ok_result(result)

        # ---- 多维表格 ----
        elif name == "feishu_list_bitables":
            result = bitable_tools.list_bitables(arguments["app_token"])
            return _ok_result(result)

        elif name == "feishu_list_bitable_fields":
            result = bitable_tools.list_bitable_fields(
                arguments["app_token"], arguments["table_id"]
            )
            return _ok_result(result)

        elif name == "feishu_read_bitable":
            result = bitable_tools.read_bitable(
                app_token=arguments["app_token"],
                table_id=arguments["table_id"],
                filter_str=arguments.get("filter", ""),
                max_records=arguments.get("max_records", 500),
            )
            return _ok_result(result)

        elif name == "feishu_add_bitable_records":
            result = bitable_tools.add_bitable_records(
                arguments["app_token"],
                arguments["table_id"],
                arguments["records"],
            )
            return _ok_result(result)

        elif name == "feishu_update_bitable_records":
            result = bitable_tools.update_bitable_records(
                arguments["app_token"],
                arguments["table_id"],
                arguments["records"],
            )
            return _ok_result(result)

        elif name == "feishu_create_bitable_table":
            result = bitable_tools.create_bitable_table(
                arguments["app_token"],
                arguments["name"],
                arguments.get("fields"),
            )
            return _ok_result(result)

        # ---- 视图管理 ----
        elif name == "feishu_list_bitable_views":
            result = bitable_tools.list_bitable_views(
                arguments["app_token"], arguments["table_id"]
            )
            return _ok_result(result)

        elif name == "feishu_create_bitable_view":
            result = bitable_tools.create_bitable_view(
                arguments["app_token"],
                arguments["table_id"],
                arguments["view_name"],
                arguments.get("view_type", "grid"),
            )
            return _ok_result(result)

        elif name == "feishu_update_bitable_view":
            result = bitable_tools.update_bitable_view(
                arguments["app_token"],
                arguments["table_id"],
                arguments["view_id"],
                arguments.get("property"),
            )
            return _ok_result(result)

        elif name == "feishu_delete_bitable_view":
            result = bitable_tools.delete_bitable_view(
                arguments["app_token"],
                arguments["table_id"],
                arguments["view_id"],
            )
            return _ok_result(result)

        # ---- 字段管理 ----
        elif name == "feishu_add_bitable_fields":
            result = bitable_tools.add_bitable_fields(
                arguments["app_token"],
                arguments["table_id"],
                arguments["fields"],
            )
            return _ok_result(result)

        elif name == "feishu_update_bitable_fields":
            result = bitable_tools.update_bitable_fields(
                arguments["app_token"],
                arguments["table_id"],
                arguments["field_updates"],
            )
            return _ok_result(result)

        elif name == "feishu_delete_bitable_fields":
            result = bitable_tools.delete_bitable_fields(
                arguments["app_token"],
                arguments["table_id"],
                arguments["field_ids"],
            )
            return _ok_result(result)

        # ---- 记录删除 ----
        elif name == "feishu_delete_bitable_records":
            result = bitable_tools.delete_bitable_records(
                arguments["app_token"],
                arguments["table_id"],
                arguments["record_ids"],
            )
            return _ok_result(result)

        # ---- 仪表盘 ----
        elif name == "feishu_list_bitable_dashboards":
            result = bitable_tools.list_bitable_dashboards(
                arguments["app_token"],
            )
            return _ok_result(result)

        elif name == "feishu_copy_bitable_dashboard":
            result = bitable_tools.copy_bitable_dashboard(
                arguments["app_token"],
                arguments["block_id"],
                arguments["name"],
            )
            return _ok_result(result)

        # ---- 消息 ----
        elif name == "feishu_send_message":
            result = message_tools.send_message(
                receive_id=arguments["receive_id"],
                content=arguments["content"],
                msg_type=arguments.get("msg_type", "text"),
                receive_id_type=arguments.get("receive_id_type", "open_id"),
            )
            return _ok_result(result)

        elif name == "feishu_send_webhook":
            result = message_tools.send_webhook(
                webhook_url=arguments["webhook_url"],
                content=arguments["content"],
                title=arguments.get("title", ""),
            )
            return _ok_result(result)

        elif name == "feishu_list_messages":
            result = message_tools.list_messages(
                chat_id=arguments.get("chat_id", ""),
                page_size=arguments.get("page_size", 20),
            )
            return _ok_result(result)

        # ---- 日历 ----
        elif name == "feishu_list_calendars":
            result = calendar_tools.list_calendars()
            return _ok_result(result)

        elif name == "feishu_list_events":
            result = calendar_tools.list_events(
                calendar_id=arguments["calendar_id"],
                start_time=arguments.get("start_time", ""),
                end_time=arguments.get("end_time", ""),
                page_size=arguments.get("page_size", 50),
            )
            return _ok_result(result)

        elif name == "feishu_create_event":
            result = calendar_tools.create_event(
                calendar_id=arguments["calendar_id"],
                summary=arguments["summary"],
                start_time=arguments["start_time"],
                end_time=arguments["end_time"],
                description=arguments.get("description", ""),
                attendees=arguments.get("attendees"),
            )
            return _ok_result(result)

        # ---- 云空间 ----
        elif name == "feishu_list_files":
            result = drive_tools.list_files(
                folder_token=arguments.get("folder_token", ""),
                page_size=arguments.get("page_size", 50),
                file_types=arguments.get("file_types"),
            )
            return _ok_result(result)

        elif name == "feishu_get_file_info":
            result = drive_tools.get_file_info(arguments["file_token"])
            return _ok_result(result)

        elif name == "feishu_search_files":
            result = drive_tools.search_files(
                query=arguments["query"],
                file_types=arguments.get("file_types"),
                count=arguments.get("count", 20),
            )
            return _ok_result(result)

        # ---- 知识库 ----
        elif name == "feishu_search_kb":
            result = wiki_tools.search_kb(
                query=arguments["query"],
                space_ids=arguments.get("space_ids"),
            )
            return _ok_result(result)

        elif name == "feishu_list_kb_spaces":
            result = wiki_tools.list_kb_spaces()
            return _ok_result(result)

        elif name == "feishu_list_kb_nodes":
            result = wiki_tools.list_kb_nodes(
                space_id=arguments["space_id"],
                parent_node_token=arguments.get("parent_node_token", ""),
            )
            return _ok_result(result)

        elif name == "feishu_get_kb_node":
            result = wiki_tools.get_kb_node(arguments["node_token"])
            return _ok_result(result)

        # ---- 审批 ----
        elif name == "feishu_list_approvals":
            result = approval_tools.list_approvals(
                status=arguments.get("status", "PENDING"),
                page_size=arguments.get("page_size", 20),
                start_time=arguments.get("start_time", ""),
                end_time=arguments.get("end_time", ""),
            )
            return _ok_result(result)

        elif name == "feishu_get_approval":
            result = approval_tools.get_approval(arguments["instance_code"])
            return _ok_result(result)

        else:
            return _error_result(f"未知工具: {name}")

    except FeishuAPIError as e:
        return _error_result(f"飞书API错误 [{e.code}]: {e.msg}")
    except ValueError as e:
        return _error_result(f"配置错误: {e}")
    except Exception as e:
        return _error_result(f"执行错误: {type(e).__name__}: {e}")


# ---- Main ----

def main():
    import asyncio
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    print("Feishu MCP Server starting...", file=sys.stderr)
    asyncio.run(run())


if __name__ == "__main__":
    main()
