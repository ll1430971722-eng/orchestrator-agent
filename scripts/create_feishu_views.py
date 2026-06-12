#!/usr/bin/env python3
"""
为现有表格创建多视图：老板看板、运营全览、看板视图

用法:
  python scripts/create_feishu_views.py
  python scripts/create_feishu_views.py --dry-run
"""
import sys
import time
from pathlib import Path

ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent
FEISHU_MCP = ORCHESTRATOR_ROOT / "mcp-servers" / "feishu"
sys.path.insert(0, str(FEISHU_MCP))

from feishu_client import get_client, FeishuAPIError

APP_TOKEN = "GPFtbIOhCafB4HsANmVcbFOan4f"

# ── 表配置 ──
TABLES = {
    "tblK15Duu70dPX6G": {
        "name": "抖音每日指标",
        "views": [
            {
                "view_name": "📊 老板看板",
                "view_type": "grid",
                "description": "筛选最近7天，只显示核心指标",
                "display_fields": [
                    "日期", "GMV（元）", "订单数", "退款率-支付口径（%）",
                    "点击-成交转化率（%）", "曝光人数", "广告消耗（元）",
                    "退款健康度", "综合体验分",
                    "一句话总结", "明日关注",
                ],
            },
            {
                "view_name": "📋 运营全览",
                "view_type": "grid",
                "description": "全部字段，按日期倒序",
            },
            {
                "view_name": "📈 渠道分析",
                "view_type": "grid",
                "description": "只看渠道相关字段",
                "display_fields": [
                    "日期",
                    "搜索GMV（元）", "搜索GMV占比（%）", "搜索环比（%）",
                    "精选联盟GMV（元）", "精选联盟GMV占比（%）", "精选联盟环比（%）",
                    "短视频GMV（元）", "短视频GMV占比（%）", "短视频环比（%）",
                    "商城GMV（元）", "商城GMV占比（%）",
                ],
            },
        ],
    },
    "tblOZGoovyt8qb0I": {
        "name": "抖音每日问题追踪",
        "views": [
            {
                "view_name": "🔴 待处理问题",
                "view_type": "grid",
                "description": "只显示待处理的问题，按优先级排序",
            },
            {
                "view_name": "📋 问题全览",
                "view_type": "grid",
                "description": "全部问题记录",
            },
            {
                "view_name": "📌 看板视图",
                "view_type": "kanban",
                "description": "按状态分组（待处理/处理中/已解决/持续观察）",
            },
        ],
    },
    "tblPj7sBL74M07dN": {
        "name": "抖音行动建议明细",
        "views": [
            {
                "view_name": "⏳ 待处理行动",
                "view_type": "grid",
                "description": "只显示待处理的行动项",
            },
            {
                "view_name": "📌 看板视图",
                "view_type": "kanban",
                "description": "按优先级分组",
            },
        ],
    },
    "tbldtOCO6pR5g7bP": {
        "name": "每日运营概览",
        "views": [
            {
                "view_name": "📊 近期概览",
                "view_type": "grid",
                "description": "按日期倒序，最近30天概览",
            },
        ],
    },
    "tblLck1taVRaxldS": {
        "name": "每日运营追踪",
        "views": [
            {
                "view_name": "⏳ 待处理",
                "view_type": "grid",
                "description": "只看待处理事项",
            },
            {
                "view_name": "📌 看板视图",
                "view_type": "kanban",
                "description": "按状态分组",
            },
        ],
    },
}


def list_existing_views(client, table_id: str) -> dict:
    """列出已有视图，返回 {view_name: view_id}"""
    resp = client.get(
        f"/bitable/v1/apps/{APP_TOKEN}/tables/{table_id}/views",
        params={"page_size": 100},
    )
    items = resp.get("data", {}).get("items", [])
    return {v["view_name"]: v["view_id"] for v in items}


def create_view(client, table_id: str, view_name: str, view_type: str) -> str:
    """创建视图，返回 view_id"""
    resp = client.post(
        f"/bitable/v1/apps/{APP_TOKEN}/tables/{table_id}/views",
        json_body={
            "view_name": view_name,
            "view_type": view_type,
        },
    )
    view = resp.get("data", {}).get("view", {})
    return view.get("view_id", "")


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("⚠️ DRY RUN 模式 — 不会实际创建\n")

    try:
        client = get_client()
    except Exception as e:
        print(f"❌ 飞书客户端初始化失败: {e}")
        sys.exit(1)

    total_created = 0

    for table_id, config in TABLES.items():
        table_name = config["name"]
        print(f"\n── {table_name} ({table_id}) ──")

        # 获取已有视图
        existing = list_existing_views(client, table_id)
        print(f"   已有视图: {list(existing.keys())}")

        for view_cfg in config["views"]:
            vn = view_cfg["view_name"]
            vt = view_cfg["view_type"]

            if vn in existing:
                print(f"   ⏭️  '{vn}' 已存在，跳过")
                continue

            if dry_run:
                print(f"   [DRY RUN] 创建 '{vn}' ({vt})")
            else:
                try:
                    vid = create_view(client, table_id, vn, vt)
                    print(f"   ✅ 创建 '{vn}' ({vt}) → {vid}")
                    total_created += 1
                    time.sleep(0.3)
                except FeishuAPIError as e:
                    print(f"   ⚠️ 创建失败: {e}")

    base_url = f"https://vcnyjz2su8ck.feishu.cn/base/{APP_TOKEN}"
    if dry_run:
        print(f"\n─── DRY RUN 预览完成 ───")
    else:
        print(f"\n✨ 共创建 {total_created} 个新视图")
    print(f"   查看 Base: {base_url}")


if __name__ == "__main__":
    main()
