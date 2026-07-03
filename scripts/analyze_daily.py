"""
日常数据分析脚本 [只读]

功能：
    读取 data/raw/ 下的 JSON 文件，计算核心运营指标。
    支持单日计算 + 7日趋势分析。

数据来源：
    - data/raw/YYYY-MM-DD/orders.json
    - data/raw/YYYY-MM-DD/products.json
    - data/raw/YYYY-MM-DD/after_sales.json
    - data/raw/YYYY-MM-DD/ads.json

输出：
    - data/processed/daily_metrics_YYYY-MM-DD.json

安全声明：
    - 只读取本地数据文件，不调用 API
    - 不做任何店铺修改操作
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import DATA_RAW, DATA_PROCESSED

# ═══════════════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════════════

def load_raw_data(date: str) -> Dict[str, Any]:
    """
    加载指定日期的原始数据。

    Args:
        date: 日期字符串 YYYY-MM-DD

    Returns:
        dict: 包含 orders, products, after_sales, ads 的字典
    """
    raw_dir = DATA_RAW / date
    data = {}

    for filename in ["orders.json", "products.json", "after_sales.json", "ads.json"]:
        filepath = raw_dir / filename
        key = filename.replace(".json", "")
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # 兼容 list 和 dict（含 data/list/records 等包装键）
                    data[key] = _unwrap_data(loaded)
            except (json.JSONDecodeError, FileNotFoundError):
                data[key] = []
        else:
            data[key] = []

    return data


def _unwrap_data(raw: Any) -> list:
    """解包各种可能的 API 响应格式，统一返回 list"""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for list_key in ("data", "items", "records", "list", "datas", "results"):
            if list_key in raw and isinstance(raw[list_key], list):
                return raw[list_key]
        # 嵌套: {"data": {"list": [...]}}
        if "data" in raw and isinstance(raw["data"], dict):
            for list_key in ("list", "items", "records"):
                if list_key in raw["data"] and isinstance(raw["data"][list_key], list):
                    return raw["data"][list_key]
    return []


def load_processed_metrics(date: str) -> Optional[Dict[str, Any]]:
    """加载已处理的指标数据"""
    filepath = DATA_PROCESSED / f"daily_metrics_{date}.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ═══════════════════════════════════════════════════
# 指标计算
# ═══════════════════════════════════════════════════

def calculate_base_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算基础运营指标。

    从 orders/after_sales/products/ads 四张原始表中提取核心指标。
    兼容多种 JSON 字段名（中英文、大小写变体）。
    """
    orders = data.get("orders", [])
    after_sales = data.get("after_sales", [])
    products = data.get("products", [])
    ads = data.get("ads", [])

    # ── 订单指标 ──
    gmv = 0.0
    order_count = 0
    buyer_count = 0

    for o in orders:
        gmv += _get_number(o, "gmv", "amount", "pay_amount", "成交金额", "支付金额", "order_amount")
        order_count += _get_count(o, order_count)
        buyer_count += _get_count(o, buyer_count, "buyer_count", "buyer_id", "成交人数", "支付人数")

    # 从 after_sales 中也尝试取订单数（兜底）
    if order_count == 0:
        for a in after_sales:
            if _get_str(a, "order_id", "订单号"):
                order_count += 1

    # ── 退款指标 ──
    refund_amount = 0.0
    refund_order_count = 0
    refund_reasons: Dict[str, int] = {}

    for a in after_sales:
        refund_amount += _get_number(a, "refund_amount", "refund_price", "退款金额", "amount")
        if _get_str(a, "refund_id", "refund_no", "退款单号", "after_sale_id"):
            refund_order_count += 1
        reason = _get_str(a, "reason", "refund_reason", "退款原因", "reason_text")
        if reason:
            refund_reasons[reason] = refund_reasons.get(reason, 0) + 1

    # ── 退款率 ──
    total_orders_for_rate = order_count + refund_order_count
    refund_rate = (refund_order_count / total_orders_for_rate * 100) if total_orders_for_rate > 0 else 0.0

    # ── 客单价 ──
    # 用支付金额算（排除退款影响）
    net_orders = order_count - refund_order_count
    avg_order_value = (gmv - refund_amount) / net_orders if net_orders > 0 else (gmv / order_count if order_count > 0 else 0.0)

    # ── 商品排行 ──
    product_gmv: Dict[str, float] = {}
    product_orders: Dict[str, int] = {}
    product_refunds: Dict[str, float] = {}

    for p in products:
        pid = _get_str(p, "product_id", "id", "商品ID", "sku_id", "spu_id") or f"product_{len(product_gmv)}"
        name = _get_str(p, "name", "title", "product_name", "商品名称", "商品标题") or pid
        p_gmv = _get_number(p, "gmv", "pay_amount", "成交金额", "amount", "total_amount")
        p_orders = int(_get_number(p, "order_count", "sold_count", "销量", "成交订单数", "sold_num"))
        p_refund = _get_number(p, "refund_amount", "退款金额")

        product_gmv[name] = product_gmv.get(name, 0) + p_gmv
        product_orders[name] = product_orders.get(name, 0) + p_orders
        product_refunds[name] = product_refunds.get(name, 0) + p_refund

    # 按 GMV 降序
    product_ranking = sorted(
        [{"name": k, "gmv": v, "orders": product_orders.get(k, 0)}
         for k, v in product_gmv.items()],
        key=lambda x: x["gmv"], reverse=True
    )
    refund_ranking = sorted(
        [{"name": k, "refund_amount": v} for k, v in product_refunds.items() if v > 0],
        key=lambda x: x["refund_amount"], reverse=True
    )

    # 退款原因 TOP5
    refund_reason_ranking = sorted(refund_reasons.items(), key=lambda x: x[1], reverse=True)[:5]

    # ── 广告指标 ──
    ad_spend = 0.0
    ad_gmv = 0.0
    ad_clicks = 0
    ad_impressions = 0

    for ad in ads:
        ad_spend += _get_number(ad, "spend", "cost", "消耗", "花费", "ad_cost")
        ad_gmv += _get_number(ad, "gmv", "pay_amount", "成交金额")
        ad_clicks += int(_get_number(ad, "click", "clicks", "点击量", "click_count"))
        ad_impressions += int(_get_number(ad, "impression", "impressions", "曝光量", "展示量", "show"))

    ad_roi = (ad_gmv / ad_spend) if ad_spend > 0 else 0.0
    ad_click_rate = (ad_clicks / ad_impressions * 100) if ad_impressions > 0 else 0.0
    ad_conversion_cost = (ad_spend / order_count) if order_count > 0 else 0.0

    # ── 数据完整性 ──
    data_completeness = {
        "orders": len(orders) > 0,
        "products": len(products) > 0,
        "after_sales": len(after_sales) > 0,
        "ads": len(ads) > 0,
    }

    return {
        "gmv": round(gmv, 2),
        "order_count": order_count,
        "buyer_count": buyer_count,
        "refund_amount": round(refund_amount, 2),
        "refund_order_count": refund_order_count,
        "refund_rate": round(refund_rate, 2),
        "avg_order_value": round(avg_order_value, 2),
        "net_gmv": round(gmv - refund_amount, 2),
        "product_ranking": product_ranking,
        "refund_ranking": refund_ranking,
        "refund_reason_ranking": [
            {"reason": r, "count": c, "pct": round(c / refund_order_count * 100, 1) if refund_order_count > 0 else 0}
            for r, c in refund_reason_ranking
        ],
        "ad_spend": round(ad_spend, 2),
        "ad_gmv": round(ad_gmv, 2),
        "ad_roi": round(ad_roi, 2),
        "ad_click_rate": round(ad_click_rate, 2),
        "ad_conversion_cost": round(ad_conversion_cost, 2),
        "ad_clicks": ad_clicks,
        "ad_impressions": ad_impressions,
        "data_completeness": data_completeness,
    }


def calculate_changes(today_metrics: Dict[str, Any], yesterday_metrics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算日环比变化。

    Args:
        today_metrics: 今日指标
        yesterday_metrics: 昨日指标（可为 None）

    Returns:
        dict: 包含环比变化百分比的字典
    """
    changes = {}

    compare_fields = [
        "gmv", "order_count", "buyer_count", "refund_amount",
        "refund_rate", "avg_order_value", "ad_spend", "ad_roi",
    ]

    for field in compare_fields:
        today_val = today_metrics.get(field, 0)
        yesterday_val = yesterday_metrics.get(field, 0) if yesterday_metrics else 0

        if yesterday_val and yesterday_val != 0:
            changes[f"{field}_change_pct"] = round((today_val - yesterday_val) / yesterday_val * 100, 2)
        elif today_val and not yesterday_val:
            changes[f"{field}_change_pct"] = None  # 昨日无数据
        else:
            changes[f"{field}_change_pct"] = 0.0

    return changes


# ═══════════════════════════════════════════════════
# 趋势分析
# ═══════════════════════════════════════════════════

def analyze_trends(dates: Optional[List[str]] = None, lookback_days: int = 7) -> Dict[str, Any]:
    """
    分析近 N 天趋势。

    加载 data/processed/ 下的历史指标，汇总趋势数据。

    Args:
        dates: 日期列表（如不提供，自动取最近 N 天）
        lookback_days: 回看天数

    Returns:
        dict: 趋势数据
    """
    if dates is None:
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(lookback_days, -1, -1)]

    trends = {
        "gmv_trend": [],
        "order_trend": [],
        "refund_rate_trend": [],
        "avg_order_value_trend": [],
        "ad_roi_trend": [],
    }

    for date in dates:
        m = load_processed_metrics(date)
        if m:
            trends["gmv_trend"].append({"date": date, "value": m.get("gmv", 0)})
            trends["order_trend"].append({"date": date, "value": m.get("order_count", 0)})
            trends["refund_rate_trend"].append({"date": date, "value": m.get("refund_rate", 0)})
            trends["avg_order_value_trend"].append({"date": date, "value": m.get("avg_order_value", 0)})
            trends["ad_roi_trend"].append({"date": date, "value": m.get("ad_roi", 0)})

    # 计算趋势方向
    for key in trends:
        values = [p["value"] for p in trends[key] if p["value"]]
        if len(values) >= 2:
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            if first_half > 0:
                trends[f"{key}_direction"] = "up" if second_half > first_half else "down"
            else:
                trends[f"{key}_direction"] = "flat"
        else:
            trends[f"{key}_direction"] = "insufficient_data"

    trends["dates_available"] = [p["date"] for p in trends["gmv_trend"]]
    return trends


# ═══════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════

def _get_number(obj: Dict, *keys: str) -> float:
    """从字典中按优先级查找数值字段，兼容中英文键名"""
    for k in keys:
        val = obj.get(k)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                continue
    return 0.0


def _get_str(obj: Dict, *keys: str) -> str:
    """从字典中按优先级查找字符串字段"""
    for k in keys:
        val = obj.get(k)
        if val and str(val).strip():
            return str(val).strip()
    return ""


def _get_count(obj: Dict, *keys) -> int:
    """如果 obj 本身被视为一条记录则返回 1，或从字段取数"""
    # 如果 keys 中只有 order_count 默认值，说明调用方只传了一个占位值，视为一条记录
    return 1


# ═══════════════════════════════════════════════════
# 输出
# ═══════════════════════════════════════════════════

def save_processed_metrics(metrics: Dict[str, Any], date: str) -> str:
    """
    保存清洗后的指标数据到 data/processed/。
    """
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    filepath = DATA_PROCESSED / f"daily_metrics_{date}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    return str(filepath)


# ═══════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"📊 日常数据分析 [只读] - {today}")
    print(f"   数据来源：{DATA_RAW}")
    print("   安全声明：只读取本地数据，不调用 API，不修改店铺数据。\n")

    # 加载数据
    raw = load_raw_data(today)

    # 检查数据是否存在
    missing = [k for k, v in raw.items() if not v]
    if len(missing) == 4:
        print(f"❌ 今日 ({today}) 无任何原始数据")
        print(f"   请先运行数据采集: /douyin-fetch-data")
        exit(1)
    elif missing:
        print(f"⚠️  部分数据缺失: {missing}")

    # 计算指标
    metrics = calculate_base_metrics(raw)

    # 计算日环比（尝试加载昨日数据）
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_metrics = load_processed_metrics(yesterday)
    changes = calculate_changes(metrics, yesterday_metrics)
    metrics.update(changes)

    # 趋势分析
    trends = analyze_trends()
    metrics["trends"] = trends

    # 保存
    output_path = save_processed_metrics(metrics, today)

    # 输出摘要
    print(f"\n{'='*50}")
    print(f"GMV:         ¥{metrics['gmv']:,.2f}")
    print(f"订单数:       {metrics['order_count']}")
    print(f"客单价:       ¥{metrics['avg_order_value']:,.2f}")
    print(f"退款率:       {metrics['refund_rate']}%")
    print(f"退款金额:     ¥{metrics['refund_amount']:,.2f}")
    if metrics.get("ad_roi", 0) > 0:
        print(f"广告ROI:      {metrics['ad_roi']:.2f}")
    print(f"{'='*50}")
    print(f"\n✅ 指标已保存到: {output_path}")

    if missing:
        print(f"\n⚠️  缺失数据: {missing}")
        print("   建议: 补充数据后再做完整分析。")
