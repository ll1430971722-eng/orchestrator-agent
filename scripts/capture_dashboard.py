#!/usr/bin/env python3
"""
Computer Use 数据采集助手

该脚本不直接自动操作浏览器，而是生成清晰的操作指令，
供 Codex 的 Computer Use 能力执行。

用法:
  python scripts/capture_dashboard.py douyin   # 输出抖音截图指令
  python scripts/capture_dashboard.py 1688     # 输出1688截图指令
  python scripts/capture_dashboard.py both     # 两个都输出（默认）

输出截图保存到: output/screenshots/{date}-{platform}-{panel}.png
"""

import sys
from pathlib import Path
from datetime import date
import json

ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ORCHESTRATOR_ROOT / "output" / "screenshots"


def _today() -> str:
    return date.today().isoformat()


def douyin_instructions(dt: str):
    return {
        "platform": "抖音小店",
        "date": dt,
        "capture_steps": [
            {
                "step": 1,
                "target": "抖店后台 → 数据 → 核心数据",
                "output": f"screenshots/{dt}-douyin-core-data.png",
                "instructions": [
                    "1. 打开浏览器，访问: https://shop.douyin.com/",
                    "2. 登录抖店后台",
                    "3. 导航到 数据 → 核心数据",
                    "4. 截图：GMV、访客数、成交件数、转化率面板",
                    "5. 保存截图到 output/screenshots/{dt}-douyin-core-data.png",
                ]
            },
            {
                "step": 2,
                "target": "抖店后台 → 数据 → 流量分析",
                "output": f"screenshots/{dt}-douyin-traffic.png",
                "instructions": [
                    "1. 导航到 数据 → 流量分析",
                    "2. 截图流量来源分布（商品卡、搜索、达人、千川、直播）",
                    "3. 保存截图到 output/screenshots/{dt}-douyin-traffic.png",
                ]
            },
            {
                "step": 3,
                "target": "抖店后台 → 店铺 → 体验分",
                "output": f"screenshots/{dt}-douyin-score.png",
                "instructions": [
                    "1. 导航到 店铺 → 体验分",
                    "2. 截图体验分详情（商品、物流、服务分项）",
                    "3. 保存截图到 output/screenshots/{dt}-douyin-score.png",
                ]
            },
        ],
        "filling_tip": "截图后，打开飞书文档，将图片拖入日报对应位置。"
    }


def _1688_instructions(dt: str):
    return {
        "platform": "1688店铺",
        "date": dt,
        "capture_steps": [
            {
                "step": 1,
                "target": "1688卖家工作台 → 数据 → 生意参谋",
                "output": f"screenshots/{dt}-1688-core.png",
                "instructions": [
                    "1. 打开浏览器，访问: https://work.1688.com/",
                    "2. 登录卖家工作台",
                    "3. 导航到 数据 → 生意参谋 → 首页",
                    "4. 截图：店铺GMV、访客数、浏览量、转化率",
                    "5. 保存截图到 output/screenshots/{dt}-1688-core.png",
                ]
            },
            {
                "step": 2,
                "target": "1688生意参谋 → 流量分析",
                "output": f"screenshots/{dt}-1688-traffic.png",
                "instructions": [
                    "1. 导航到 生意参谋 → 流量 → 流量概况",
                    "2. 截图流量来源分布（搜索流量、推荐流量、活动流量等）",
                    "3. 保存截图到 output/screenshots/{dt}-1688-traffic.png",
                ]
            },
            {
                "step": 3,
                "target": "1688卖家工作台 → 店铺 → 店铺评分",
                "output": f"screenshots/{dt}-1688-bsr.png",
                "instructions": [
                    "1. 导航到 店铺管理 → 店铺评分（BSR）",
                    "2. 截图BSR评分详情",
                    "3. 保存截图到 output/screenshots/{dt}-1688-bsr.png",
                ]
            },
        ],
        "filling_tip": "截图后，打开飞书文档，将图片拖入日报对应位置。"
    }


def main():
    dt = _today()
    platforms = []
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "both":
            platforms = ["douyin", "1688"]
        else:
            platforms = [arg]
    else:
        platforms = ["douyin", "1688"]

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 56)
    print("  Computer Use 数据采集指令")
    print(f"  日期: {dt}")
    print("=" * 56)
    print()

    for p in platforms:
        if p == "douyin":
            plan = douyin_instructions(dt)
        elif p == "1688":
            plan = _1688_instructions(dt)
        else:
            print(f"⚠️ 不支持的平台: {p}，可用: douyin / 1688 / both")
            continue

        print(f"▶ 平台: {plan['platform']}")
        print()
        for step in plan["capture_steps"]:
            print(f"  Step {step['step']}: {step['target']}")
            print(f"  截图 → {step['output']}")
            for instr in step["instructions"]:
                print(f"    {instr}")
            print()
        print(f"  提示: {plan['filling_tip']}")
        print()

    print("=" * 56)
    print("  把上面的指令交给 Codex，它能用 Computer Use 自动执行")
    print("  或者复制到 playbook/workflow 中每日自动运行")
    print("=" * 56)

    # 同时输出 JSON 格式供程序化调用
    json_path = OUTPUT_DIR / f"{dt}-capture-plan.json"
    result = {"date": dt, "platforms": {}}
    for p in platforms:
        if p == "douyin":
            result["platforms"][p] = douyin_instructions(dt)
        elif p == "1688":
            result["platforms"][p] = _1688_instructions(dt)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n📋 采集计划已保存: {json_path}")


if __name__ == "__main__":
    main()
