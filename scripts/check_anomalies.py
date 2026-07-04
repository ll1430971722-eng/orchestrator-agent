#!/usr/bin/env python3
"""
检测运营数据异常，生成预警提醒

读取 output/reports/ 下的日报，检查是否有需要注意的信号。
输出到 output/alerts/ 目录，或直接打印。

用法:
  python scripts/check_anomalies.py              # 检查今天
  python scripts/check_anomalies.py 2026-07-04   # 检查指定日期
"""

import sys
import re
from pathlib import Path
from datetime import date, datetime

ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ORCHESTRATOR_ROOT / "output" / "reports"
ALERTS_DIR = ORCHESTRATOR_ROOT / "output" / "alerts"


def extract_number(text: str) -> float:
    """从文本中提取数字，如 '78.03' """
    m = re.search(r'(\d+\.?\d*)', text)
    return float(m.group(1)) if m else 0.0


def check_douyin_report(path: Path) -> list:
    """检查抖音日报，返回警告列表"""
    content = path.read_text(encoding="utf-8")
    warnings = []

    # 检查体验分
    score_match = re.search(r'体验分.*?(\d+\.?\d*)', content)
    if score_match:
        score = float(score_match.group(1))
        if score < 4.0:
            warnings.append(f"🔴 体验分 {score}！低于4.0，流量将受限制")
        elif score < 4.5:
            warnings.append(f"🟡 体验分 {score}，建议关注，目标 > 4.5")

    # 检查转化率
    conv_match = re.search(r'转化率.*?(\d+\.?\d*)', content)
    if conv_match:
        conv = float(conv_match.group(1))
        if conv < 1.0:
            warnings.append(f"🔴 转化率 {conv}%，低于1%，需要排查原因")
        elif conv < 2.0:
            warnings.append(f"🟡 转化率 {conv}%，偏低")

    # 检查 GMV 异常
    gmv_match = re.search(r'GMV[：:].*?(\d+\.?\d*)', content)
    if gmv_match:
        gmv = float(gmv_match.group(1))
        if gmv == 0:
            warnings.append("🔴 GMV 为 0！检查是否有订单进来")

    # 检查空字段（运营没填）
    blanks = content.count("|  |") + content.count("|-")
    if blanks > 5:
        warnings.append(f"🟡 日报有 {blanks} 个空字段未填写")

    return warnings


def check_1688_report(path: Path) -> list:
    """检查1688日报，返回警告列表"""
    content = path.read_text(encoding="utf-8")
    warnings = []

    score_match = re.search(r'BSR.*?(\d+\.?\d*)', content)
    if score_match:
        score = float(score_match.group(1))
        if score < 4.0:
            warnings.append(f"🔴 BSR评分 {score}！低于4.0将降权")
        elif score < 4.5:
            warnings.append(f"🟡 BSR评分 {score}，建议关注")

    gmv_match = re.search(r'GMV[：:].*?(\d+\.?\d*)', content)
    if gmv_match:
        gmv = float(gmv_match.group(1))
        if gmv == 0:
            warnings.append("🔴 GMV 为 0！检查是否有订单进来")

    blanks = content.count("|  |") + content.count("|-")
    if blanks > 5:
        warnings.append(f"🟡 日报有 {blanks} 个空字段未填写")

    return warnings


def main():
    # 日期
    dt = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    try:
        datetime.strptime(dt, "%Y-%m-%d")
    except ValueError:
        print(f"❌ 日期格式: {dt}")
        sys.exit(1)

    ALERTS_DIR.mkdir(parents=True, exist_ok=True)

    all_warnings = {"douyin": [], "1688": []}

    for platform in ["douyin", "1688"]:
        report_path = REPORTS_DIR / f"{dt}-{platform}-report.md"
        if not report_path.exists():
            print(f"ℹ️ {platform} 日报不存在: {report_path}，跳过")
            continue

        if platform == "douyin":
            all_warnings[platform] = check_douyin_report(report_path)
        else:
            all_warnings[platform] = check_1688_report(report_path)

    # 输出
    print(f"📊 运营数据异常检查 — {dt}")
    print("=" * 44)
    has_alerts = False

    for platform, warnings in all_warnings.items():
        platform_name = "抖音小店" if platform == "douyin" else "1688店铺"
        print(f"\n▶ {platform_name}:")
        if warnings:
            has_alerts = True
            for w in warnings:
                print(f"  {w}")
        else:
            print(f"  ✅ 无异常")

    if not has_alerts:
        print(f"\n✅ 所有数据正常")

    # 保存到文件
    alert_path = ALERTS_DIR / f"{dt}-alerts.md"
    with open(alert_path, "w", encoding="utf-8") as f:
        f.write(f"# 运营异常检查 — {dt}\n\n")
        for platform, warnings in all_warnings.items():
            pn = "抖音小店" if platform == "douyin" else "1688店铺"
            f.write(f"## {pn}\n")
            for w in warnings:
                f.write(f"- {w}\n")
            if not warnings:
                f.write("- 无异常\n")
            f.write("\n")
    print(f"\n📋 预警报告已保存: {alert_path}")


if __name__ == "__main__":
    main()
