#!/usr/bin/env python3
"""
升级飞书多维表格字段类型：让数字变成货币/进度条/星星评分。

用法:
  python scripts/upgrade_feishu_tables.py
  python scripts/upgrade_feishu_tables.py --dry-run    # 只看不改
"""
import sys
import os
import time
from pathlib import Path

ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent
FEISHU_MCP = ORCHESTRATOR_ROOT / "mcp-servers" / "feishu"
sys.path.insert(0, str(FEISHU_MCP))

from feishu_client import get_client, FeishuAPIError

APP_TOKEN = "GPFtbIOhCafB4HsANmVcbFOan4f"
METRICS_TABLE_ID = "tblK15Duu70dPX6G"

# ═══════════════════════════════════════════════════
# 字段分类规则
# ═══════════════════════════════════════════════════

MONEY_KEYWORDS = [
    "GMV", "金额", "客单价", "广告消耗", "广告投放",
]

PERCENT_KEYWORDS = [
    "率", "占比", "环比", "变化",
]

SCORE_KEYWORDS = [
    "评分", "体验分",
]

# 手动指定（优先级高于关键词匹配）
MONEY_FIELDS = {
    "GMV（元）", "客单价（元）", "同行客单价基准（元）",
    "广告消耗（元）", "退款金额-退款口径（元）", "7日累计退款金额（元）",
    "搜索GMV（元）", "精选联盟GMV（元）", "短视频GMV（元）", "商城GMV（元）",
}

PERCENT_FIELDS = {
    "GMV较昨日变化（%）", "订单数较昨日变化（%）", "客单价较昨日变化（%）",
    "退款率-支付口径（%）", "退款率较昨日变化（%）", "7日累计退款率（%）",
    "退款原因TOP1占比（%）", "退款原因TOP2占比（%）",
    "曝光-点击率（%）", "曝光-点击率较昨日变化（%）", "同行曝光-点击率标杆（%）",
    "点击-成交转化率（%）", "点击-成交转化率较昨日变化（%）", "同行点击-成交率基准（%）",
    "曝光较昨日变化（%）",
    "搜索GMV占比（%）", "搜索环比（%）",
    "精选联盟GMV占比（%）", "精选联盟环比（%）",
    "短视频GMV占比（%）", "短视频环比（%）",
    "商城GMV占比（%）",
}

SCORE_FIELDS = {
    "店铺总评分", "商品体验分", "物流体验分", "服务体验分",
}

# 新增公式字段
FORMULA_FIELDS = [
    {
        "field_name": "退款健康度",
        "type": 20,
        "property": {
            "formula_expression": (
                'IF([退款率-支付口径（%）] > 15, "🔴 严重", '
                'IF([退款率-支付口径（%）] > 8, "🟡 注意", "🟢 健康"))'
            )
        },
    },
    {
        "field_name": "综合体验分",
        "type": 20,
        "property": {
            "formula_expression": "([商品体验分] + [物流体验分] + [服务体验分]) / 3"
        },
    },
]

# ═══════════════════════════════════════════════════
# 主逻辑
# ═══════════════════════════════════════════════════


def list_fields(client):
    """列出指标表所有字段"""
    resp = client.get(
        f"/bitable/v1/apps/{APP_TOKEN}/tables/{METRICS_TABLE_ID}/fields",
        params={"page_size": 200},
    )
    items = resp.get("data", {}).get("items", [])
    return {
        f["field_name"]: {"field_id": f["field_id"], "type": f.get("type", 0)}
        for f in items
    }


def update_field_ui_type(client, field_id: str, field_name: str, ui_type: str, property_overrides: dict = None):
    """更新字段的 ui_type，保留原有字段名和类型"""
    body = {
        "field_name": field_name,
        "type": 2,  # Number
        "ui_type": ui_type,
    }
    if property_overrides:
        body["property"] = property_overrides
    try:
        resp = client.put(
            f"/bitable/v1/apps/{APP_TOKEN}/tables/{METRICS_TABLE_ID}/fields/{field_id}",
            json_body=body,
        )
        return True, resp
    except FeishuAPIError as e:
        return False, str(e)


def add_formula_field(client, field_def: dict):
    """新增公式字段"""
    try:
        resp = client.post(
            f"/bitable/v1/apps/{APP_TOKEN}/tables/{METRICS_TABLE_ID}/fields",
            json_body=field_def,
        )
        field = resp.get("data", {}).get("field", {})
        return True, field.get("field_id", "")
    except FeishuAPIError as e:
        return False, str(e)


def normalize_progress_values(client, field_name: str, field_map: dict):
    """将百分比字段的值从 15.3 归一化到 0.153（Progress ui_type 需要 0-1 范围）"""
    field_id = field_map.get(field_name, {}).get("field_id", "")
    if not field_id:
        return 0, 0

    # 读取所有记录
    records = client.paginated_get(
        f"/bitable/v1/apps/{APP_TOKEN}/tables/{METRICS_TABLE_ID}/records",
        item_key="items",
        max_pages=20,
    )

    updated = 0
    skipped = 0
    for record in records:
        record_id = record.get("record_id", "")
        fields = record.get("fields", {})
        value = fields.get(field_name)

        if value is None:
            continue
        if not isinstance(value, (int, float)):
            continue

        # 如果值 > 1 且 < 10000，很可能是百分比格式，需要归一化
        # 如果值已经在 0-1 范围（如 0.153），跳过
        if 1.0 < abs(value) <= 10000:
            normalized = value / 100.0
            try:
                client.put(
                    f"/bitable/v1/apps/{APP_TOKEN}/tables/{METRICS_TABLE_ID}/records/{record_id}",
                    json_body={"fields": {field_name: normalized}},
                )
                updated += 1
            except FeishuAPIError:
                skipped += 1
        else:
            skipped += 1

    return updated, skipped


def main():
    dry_run = "--dry-run" in sys.argv

    print("🔧 飞书多维表格字段美化工具\n")
    print(f"   Base: {APP_TOKEN}")
    print(f"   表: {METRICS_TABLE_ID}")
    if dry_run:
        print("   ⚠️ DRY RUN 模式 — 不会实际修改\n")

    # 连接
    try:
        client = get_client()
    except Exception as e:
        print(f"❌ 飞书客户端初始化失败: {e}")
        sys.exit(1)

    # 获取当前字段列表
    print("📋 获取当前字段...")
    field_map = list_fields(client)
    print(f"   共 {len(field_map)} 个字段\n")

    # ── Step 1: 升级金额字段 → Currency ──
    print("💰 升级金额字段 → Currency（¥符号 + 千分位）")
    money_count = 0
    for fn in MONEY_FIELDS:
        if fn in field_map:
            fid = field_map[fn]["field_id"]
            if dry_run:
                print(f"   [DRY RUN] {fn} → Currency")
            else:
                ok, msg = update_field_ui_type(client, fid, fn, "Currency", {
                    "decimal_places": 2,
                    "use_separate": True,
                })
                if ok:
                    print(f"   ✅ {fn} → Currency")
                else:
                    print(f"   ⚠️ {fn} 更新失败: {msg}")
                time.sleep(0.3)
            money_count += 1
    print(f"   共 {money_count} 个金额字段\n")

    # ── Step 2: 升级百分比字段 → Progress ──
    print("📊 升级百分比字段 → Progress（进度条）")
    progress_count = 0
    for fn in PERCENT_FIELDS:
        if fn in field_map:
            fid = field_map[fn]["field_id"]

            # 先归一化数据（Progress 需要 0-1 范围）
            if not dry_run:
                updated, skipped = normalize_progress_values(client, fn, field_map)
                if updated > 0:
                    print(f"   📝 {fn}: 归一化 {updated} 条 (skipped {skipped})")
                time.sleep(0.5)

            if dry_run:
                print(f"   [DRY RUN] {fn} → Progress")
            else:
                ok, msg = update_field_ui_type(client, fid, fn, "Progress", {
                    "range": {"min": 0, "max": 1},
                })
                if ok:
                    print(f"   ✅ {fn} → Progress")
                else:
                    print(f"   ⚠️ {fn} 更新失败: {msg}")
                time.sleep(0.3)
            progress_count += 1
    print(f"   共 {progress_count} 个百分比字段\n")

    # ── Step 3: 升级评分字段 → Rating ──
    print("⭐ 升级评分字段 → Rating（星星）")
    score_count = 0
    for fn in SCORE_FIELDS:
        if fn in field_map:
            fid = field_map[fn]["field_id"]
            if dry_run:
                print(f"   [DRY RUN] {fn} → Rating")
            else:
                ok, msg = update_field_ui_type(client, fid, fn, "Rating", {
                    "rating": {"max": 5, "icon": "star"},
                })
                if ok:
                    print(f"   ✅ {fn} → Rating（五星）")
                else:
                    print(f"   ⚠️ {fn} 更新失败: {msg}")
                time.sleep(0.3)
            score_count += 1
    print(f"   共 {score_count} 个评分字段\n")

    # ── Step 4: 新增公式字段 ──
    print("🧮 新增公式字段")
    formula_count = 0
    for fdef in FORMULA_FIELDS:
        fn = fdef["field_name"]
        if fn in field_map:
            print(f"   ⏭️ {fn} 已存在，跳过")
            continue
        if dry_run:
            print(f"   [DRY RUN] 新增: {fn}")
        else:
            ok, msg = add_formula_field(client, fdef)
            if ok:
                print(f"   ✅ {fn} 创建成功 ({msg})")
            else:
                print(f"   ⚠️ {fn} 创建失败: {msg}")
            time.sleep(0.3)
        formula_count += 1
    print(f"   共 {formula_count} 个公式字段\n")

    # ── 完成 ──
    base_url = f"https://vcnyjz2su8ck.feishu.cn/base/{APP_TOKEN}"
    table_url = f"{base_url}/table/{METRICS_TABLE_ID}"

    if dry_run:
        print("─── DRY RUN 完成，以上是不会实际执行的预览 ───")
    else:
        print(f"✨ 美化完成！")
    print(f"   查看表格: {table_url}")
    print(f"\n💡 提示: 条件格式/颜色规则需要在飞书 UI 中手动设置（API不支持）")
    print(f"   建议设置: 退款率>15% 红色, 评分<80 红色, 转化率>3% 绿色")


if __name__ == "__main__":
    main()
