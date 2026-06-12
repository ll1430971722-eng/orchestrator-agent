#!/usr/bin/env python3
"""
创建飞书多维表格：抖音每日指标 + 抖音每日问题追踪
"""
import sys
from pathlib import Path

ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent
FEISHU_MCP = ORCHESTRATOR_ROOT / "mcp-servers" / "feishu"
sys.path.insert(0, str(FEISHU_MCP))

from feishu_client import get_client, FeishuAPIError

APP_TOKEN = "GPFtbIOhCafB4HsANmVcbFOan4f"


def create_table(client, name: str, fields: list) -> dict:
    """创建数据表"""
    resp = client.post(
        f"/bitable/v1/apps/{APP_TOKEN}/tables",
        json_body={
            "table": {
                "name": name,
                "fields": fields,
            }
        },
    )
    table = resp.get("data", {}).get("table", {}) or resp.get("data", {})
    return {
        "table_id": table.get("table_id", ""),
        "name": table.get("name", name),
    }


def create_table1(client):
    """创建 抖音每日指标 表"""
    fields = [
        # ── GMV & 订单 ──
        {"field_name": "日期", "type": 5},
        {"field_name": "GMV（元）", "type": 2},
        {"field_name": "GMV较昨日变化（%）", "type": 2},
        {"field_name": "订单数", "type": 2},
        {"field_name": "订单数较昨日变化（%）", "type": 2},
        {"field_name": "客单价（元）", "type": 2},
        {"field_name": "客单价较昨日变化（%）", "type": 2},
        {"field_name": "同行客单价基准（元）", "type": 2},

        # ── 流量 & 转化 ──
        {"field_name": "曝光人数", "type": 2},
        {"field_name": "曝光较昨日变化（%）", "type": 2},
        {"field_name": "曝光-点击率（%）", "type": 2},
        {"field_name": "曝光-点击率较昨日变化（%）", "type": 2},
        {"field_name": "同行曝光-点击率标杆（%）", "type": 2},
        {"field_name": "点击-成交转化率（%）", "type": 2},
        {"field_name": "点击-成交转化率较昨日变化（%）", "type": 2},
        {"field_name": "同行点击-成交率基准（%）", "type": 2},
        {"field_name": "成交人数", "type": 2},
        {"field_name": "同行成交人数基准", "type": 2},
        {"field_name": "广告消耗（元）", "type": 2},

        # ── 退款 ──
        {"field_name": "退款率-支付口径（%）", "type": 2},
        {"field_name": "退款率较昨日变化（%）", "type": 2},
        {"field_name": "退款金额-退款口径（元）", "type": 2},
        {"field_name": "退款订单数", "type": 2},
        {"field_name": "7日累计退款金额（元）", "type": 2},
        {"field_name": "7日累计退款率（%）", "type": 2},
        {"field_name": "退款原因TOP1", "type": 1},
        {"field_name": "退款原因TOP1占比（%）", "type": 2},
        {"field_name": "退款原因TOP2", "type": 1},
        {"field_name": "退款原因TOP2占比（%）", "type": 2},

        # ── 渠道（近7天）──
        {"field_name": "搜索GMV（元）", "type": 2},
        {"field_name": "搜索GMV占比（%）", "type": 2},
        {"field_name": "搜索环比（%）", "type": 2},
        {"field_name": "精选联盟GMV（元）", "type": 2},
        {"field_name": "精选联盟GMV占比（%）", "type": 2},
        {"field_name": "精选联盟环比（%）", "type": 2},
        {"field_name": "短视频GMV（元）", "type": 2},
        {"field_name": "短视频GMV占比（%）", "type": 2},
        {"field_name": "短视频环比（%）", "type": 2},
        {"field_name": "商城GMV（元）", "type": 2},
        {"field_name": "商城GMV占比（%）", "type": 2},

        # ── 店铺评分 ──
        {"field_name": "店铺总评分", "type": 2},
        {"field_name": "商品体验分", "type": 2},
        {"field_name": "物流体验分", "type": 2},
        {"field_name": "服务体验分", "type": 2},

        # ── 商品健康度 ──
        {"field_name": "优秀商品数", "type": 2},
        {"field_name": "有销量商品数", "type": 2},
        {"field_name": "零销量商品数", "type": 2},
        {"field_name": "待发货订单数", "type": 2},
        {"field_name": "待处理售后数", "type": 2},

        # ── 总结（文本）──
        {"field_name": "一句话总结", "type": 1},
        {"field_name": "漏斗概况", "type": 1},
        {"field_name": "渠道亮点", "type": 1},
        {"field_name": "明日关注", "type": 1},
    ]

    result = create_table(client, "抖音每日指标", fields)
    print(f"✅ 表1创建成功: {result['name']}")
    print(f"   table_id: {result['table_id']}")
    print(f"   字段数: {len(fields)}")
    return result["table_id"]


def create_table2(client):
    """创建 抖音每日问题追踪 表"""
    fields = [
        {"field_name": "日期", "type": 5},
        {"field_name": "优先级",
         "type": 3,
         "property": {
             "options": [
                 {"name": "🔴严重", "color": 1},
                 {"name": "🟡注意", "color": 2},
                 {"name": "🟢观察", "color": 3},
             ]
         }},
        {"field_name": "问题标题", "type": 1},
        {"field_name": "数据依据", "type": 1},
        {"field_name": "业务影响", "type": 1},
        {"field_name": "根因分析", "type": 1},
        {"field_name": "解决建议", "type": 1},
        {"field_name": "新手解释", "type": 1},
        {"field_name": "状态",
         "type": 3,
         "property": {
             "options": [
                 {"name": "待处理", "color": 1},
                 {"name": "处理中", "color": 2},
                 {"name": "已解决", "color": 3},
                 {"name": "持续观察", "color": 4},
             ]
         }},
        {"field_name": "来源报告", "type": 1},
    ]

    result = create_table(client, "抖音每日问题追踪", fields)
    print(f"✅ 表2创建成功: {result['name']}")
    print(f"   table_id: {result['table_id']}")
    print(f"   字段数: {len(fields)}")
    return result["table_id"]


def main():
    try:
        client = get_client()
    except Exception as e:
        print(f"❌ 飞书客户端初始化失败: {e}")
        sys.exit(1)

    print(f"🚀 在 Base {APP_TOKEN} 中创建表...\n")

    table1_id = create_table1(client)
    print()
    table2_id = create_table2(client)

    base_url = f"https://vcnyjz2su8ck.feishu.cn/base/{APP_TOKEN}"
    print(f"\n✨ 完成!")
    print(f"   表1: {base_url}/table/{table1_id}")
    print(f"   表2: {base_url}/table/{table2_id}")
    print(f"\n请保存这两个 table_id 用于后续数据同步:")

    # 输出配置
    print(f"\n# 飞书表配置")
    print(f"DAILY_METRICS_TABLE_ID = {table1_id!r}")
    print(f"PROBLEM_TRACKING_TABLE_ID = {table2_id!r}")


if __name__ == "__main__":
    main()
