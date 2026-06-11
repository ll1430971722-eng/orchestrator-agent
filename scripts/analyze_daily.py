"""
日常数据分析脚本 [只读]

功能：
    读取 data/raw/ 下的 JSON/CSV 文件，生成基础分析。
    计算核心指标，识别异常。

数据来源：
    - data/raw/YYYY-MM-DD/orders.json
    - data/raw/YYYY-MM-DD/products.json
    - data/raw/YYYY-MM-DD/after_sales.json
    - data/raw/YYYY-MM-DD/ads.json

输出：
    - data/processed/daily_metrics.json — 清洗后的结构化指标

安全声明：
    - 只读取本地数据文件，不调用 API
    - 不做任何店铺修改操作

第一版：基础分析框架，从本地 JSON/CSV 读取数据。
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


def load_raw_data(date: str) -> Dict[str, Any]:
    """
    加载指定日期的原始数据。

    Args:
        date: 日期字符串 YYYY-MM-DD

    Returns:
        dict: 包含 orders, products, after_sales, ads 的字典
    """
    raw_dir = f"data/raw/{date}"
    data = {}

    for filename in ["orders.json", "products.json", "after_sales.json", "ads.json"]:
        filepath = os.path.join(raw_dir, filename)
        key = filename.replace(".json", "")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data[key] = json.load(f)
        else:
            data[key] = []

    return data


def calculate_base_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算基础运营指标。

    Args:
        data: 原始数据字典

    Returns:
        dict: 基础指标
    """
    metrics = {
        "gmv": 0.0,
        "order_count": 0,
        "refund_amount": 0.0,
        "refund_rate": 0.0,
        "avg_order_value": 0.0,
        "product_ranking": [],
        "refund_ranking": [],
        "data_completeness": {},
    }

    # TODO: 根据实际数据格式实现指标计算
    # 1. 遍历 orders 计算 GMV、订单数
    # 2. 遍历 after_sales 计算退款金额、退款率
    # 3. 计算客单价
    # 4. 生成商品排行

    # 标记数据完整性
    metrics["data_completeness"] = {
        "orders": len(data.get("orders", [])) > 0,
        "products": len(data.get("products", [])) > 0,
        "after_sales": len(data.get("after_sales", [])) > 0,
        "ads": len(data.get("ads", [])) > 0,
    }

    return metrics


def analyze_trends(dates: list, data_dir: str = "data/processed") -> Dict[str, Any]:
    """
    分析近 7 天趋势。

    Args:
        dates: 日期列表
        data_dir: 数据目录

    Returns:
        dict: 趋势分析结果
    """
    trends = {
        "gmv_trend": [],
        "order_trend": [],
        "refund_rate_trend": [],
    }
    # TODO: 加载历史数据，计算趋势变化
    return trends


def save_processed_metrics(metrics: Dict[str, Any], date: str) -> str:
    """
    保存清洗后的指标数据。

    Args:
        metrics: 指标数据
        date: 日期字符串

    Returns:
        str: 保存路径
    """
    processed_dir = "data/processed"
    os.makedirs(processed_dir, exist_ok=True)

    filepath = os.path.join(processed_dir, f"daily_metrics_{date}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    return filepath


if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"日常数据分析 [只读] - {today}")
    print("数据来源：data/raw/ 下的本地 JSON/CSV 文件")
    print("安全声明：只读取本地数据，不调用 API，不修改店铺数据。")

    # 加载数据
    raw = load_raw_data(today)

    # 计算指标
    metrics = calculate_base_metrics(raw)

    # 保存结果
    output_path = save_processed_metrics(metrics, today)
    print(f"分析结果已保存到 {output_path}")

    # 数据完整性提示
    missing = [k for k, v in metrics["data_completeness"].items() if not v]
    if missing:
        print(f"⚠️  以下数据缺失：{missing}")
        print("   建议：补充相应数据后再进行分析。")
