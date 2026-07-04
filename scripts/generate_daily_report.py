#!/usr/bin/env python3
"""
生成每日运营日报（markdown 格式）

用法:
  python scripts/generate_daily_report.py             # 今天，两个店铺
  python scripts/generate_daily_report.py 2026-07-04      # 指定日期
  python scripts/generate_daily_report.py 2026-07-04 douyin  # 仅抖音
  python scripts/generate_daily_report.py 2026-07-04 1688   # 仅1688

输出: output/reports/{date}-{platform}-report.md
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date
import shutil

ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ORCHESTRATOR_ROOT / "report-templates"
OUTPUT_DIR = ORCHESTRATOR_ROOT / "output" / "reports"


def generate_report(report_date: str, platform: str) -> str:
    """从模板生成日报，返回输出文件路径"""
    template_file = TEMPLATES_DIR / f"{platform}_template.md"
    if not template_file.exists():
        print(f"❌ 模板不存在: {template_file}")
        sys.exit(1)

    content = template_file.read_text(encoding="utf-8")
    content = content.replace("{date}", report_date)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{report_date}-{platform}-report.md"
    out_path.write_text(content, encoding="utf-8")
    return str(out_path)


def main():
    today = date.today()
    report_date = sys.argv[1] if len(sys.argv) > 1 else today.isoformat()

    # 校验日期格式
    try:
        datetime.strptime(report_date, "%Y-%m-%d")
    except ValueError:
        print(f"❌ 日期格式错误，请使用 YYYY-MM-DD，输入为: {report_date}")
        sys.exit(1)

    platforms = []
    if len(sys.argv) > 2:
        platforms = [sys.argv[2]]
    else:
        platforms = ["douyin", "1688"]

    for platform in platforms:
        path = generate_report(report_date, platform)
        print(f"✅ 已生成 {platform} 日报: {path}")

    print(f"\n在飞书上操作：")
    print(f"  1. 打开飞书 → 新建文档")
    print(f"  2. 内容粘贴或拖拽进去")
    print(f"  3. 发给运营填写，或你自己填上从后台查到的数据")


if __name__ == "__main__":
    main()
