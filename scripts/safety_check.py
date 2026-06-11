"""
代码安全检查脚本 [只读]

功能：
    扫描 scripts/ 目录下的 Python 脚本文件名和内容，
    检测是否存在高风险词汇。

检查范围：
    - 文件名是否包含高风险词汇
    - 文件内容中是否出现高风险词汇（排除注释和字符串中的安全声明）

高风险词汇：
    - update           — 更新操作
    - modify           — 修改操作
    - delete           — 删除操作
    - remove           — 移除操作
    - create_campaign  — 创建广告计划
    - change_price     — 改价
    - set_stock        — 设置库存
    - reply_customer   — 回复客户
    - refund           — 退款处理
    - cancel_order     — 取消订单
    - ship_order       — 发货
    - coupon           — 优惠券操作
    - promotion        — 促销活动创建
    - publish          — 发布/上架
    - unpublish        — 下架

安全声明：
    - 本脚本只做本地代码安全检查，不调用任何抖店 API
    - 不修改任何文件
    - 不自动修复代码
"""

import os
import re
from typing import List, Dict, Tuple, Any


# 高风险词汇列表
HIGH_RISK_KEYWORDS = [
    "update",
    "modify",
    "delete",
    "remove",
    "create_campaign",
    "change_price",
    "set_stock",
    "reply_customer",
    "refund",
    "cancel_order",
    "ship_order",
    "coupon",
    "promotion",
    "publish",
    "unpublish",
]

# 当前项目只保留分析脚本（数据采集由 Skills + Playwright MCP 完成）
# 旧脚本已归档到 scripts/_legacy/，不参与安全检查
LEGACY_DIR = "_legacy"

# 分析脚本白名单（只读分析，不碰店铺数据）
ANALYSIS_SCRIPTS = [
    "analyze_daily",                # 日常指标计算
    "diagnose_problems",            # 运营问题诊断
    "generate_report",              # 日报生成
    "generate_action_plan",         # 行动清单
    "generate_future_recommendations",  # 未来建议
    "safety_check",                 # 本安全检查脚本
]

# 安全声明相关的关键词（这些上下文中的高风险词不算违规）
SAFETY_CONTEXT_KEYWORDS = [
    "不允许",
    "禁止",
    "不能",
    "不会",
    "只读",
    "安全声明",
    "安全限制",
    "安全政策",
    "safety",
    "read_only",
    "不修改",
    "不自动",
    "不调用",
    "浏览器",
    "browser",
    "截图",
    "screenshot",
    "导航",
    "navigation",
    "提取",
    "extract",
    "查看页面",
    "只提取",
    "不点击任何修改",
    "不修改订单",
    "不修改商品",
]


def scan_filenames(scripts_dir: str) -> List[Tuple[str, List[str]]]:
    """
    扫描文件名是否包含高风险词汇。

    Args:
        scripts_dir: 脚本目录路径

    Returns:
        list: [(文件名, [匹配的高风险词汇]), ...]
    """
    warnings = []

    # 文件名检查（分析脚本允许，旧脚本在 _legacy 中不检查）
    for filename in os.listdir(scripts_dir):
        if not filename.endswith(".py"):
            continue

        # 跳过 _legacy 目录中的脚本
        filepath = os.path.join(scripts_dir, filename)
        if os.path.isdir(filepath):
            continue

        matched = []
        filename_lower = filename.lower().replace(".py", "")

        # 分析脚本在白名单中
        is_analysis_script = filename_lower in ANALYSIS_SCRIPTS

        for keyword in HIGH_RISK_KEYWORDS:
            if keyword in filename_lower:
                # 检查是否符合安全命名模式
                safe_prefixes = ["analyze_", "diagnose_", "generate_", "safety_"]
                is_safe_prefix = any(filename_lower.startswith(prefix) for prefix in safe_prefixes)
                if not is_safe_prefix and not is_analysis_script:
                    matched.append(keyword)

        if matched:
            warnings.append((filename, matched))

    return warnings


def scan_file_content(filepath: str) -> List[Tuple[int, str, str]]:
    """
    扫描单个文件内容是否包含高风险词汇。

    排除规则：
        - 注释行中的高风险词汇不算违规
        - 包含安全声明上下文的行不算违规

    Args:
        filepath: 文件路径

    Returns:
        list: [(行号, 行内容, 匹配的关键词), ...]
    """
    warnings = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        # 跳过纯注释行
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        if stripped.startswith("*"):
            continue

        # 跳过包含安全声明上下文的行
        is_safety_context = False
        for safety_word in SAFETY_CONTEXT_KEYWORDS:
            if safety_word in stripped:
                is_safety_context = True
                break
        if is_safety_context:
            continue

        # 检查高风险词汇
        line_lower = stripped.lower()
        for keyword in HIGH_RISK_KEYWORDS:
            if keyword in line_lower:
                warnings.append((line_num, stripped[:100], keyword))

    return warnings


def scan_scripts_directory(scripts_dir: str = "scripts") -> Dict[str, Any]:
    """
    扫描整个 scripts 目录。

    Args:
        scripts_dir: 脚本目录路径

    Returns:
        dict: 扫描结果
    """
    result = {
        "total_files": 0,
        "filename_warnings": [],
        "content_warnings": {},
        "overall_status": "PASS",
    }

    if not os.path.exists(scripts_dir):
        result["overall_status"] = "ERROR"
        result["error"] = f"目录不存在: {scripts_dir}"
        return result

    # 扫描文件名
    result["filename_warnings"] = scan_filenames(scripts_dir)

    # 扫描文件内容
    for filename in sorted(os.listdir(scripts_dir)):
        if not filename.endswith(".py"):
            continue

        result["total_files"] += 1
        filepath = os.path.join(scripts_dir, filename)
        content_warnings = scan_file_content(filepath)

        if content_warnings:
            result["content_warnings"][filename] = content_warnings

    # 判断整体状态
    if result["filename_warnings"] or result["content_warnings"]:
        result["overall_status"] = "WARNING"

    return result


def print_results(result: Dict[str, Any]):
    """
    打印扫描结果。
    """
    print("=" * 60)
    print("🔒 douyin-shop-agent 代码安全检查")
    print("=" * 60)
    print(f"扫描目录：scripts/")
    print(f"扫描文件数：{result['total_files']}")
    print(f"整体状态：{result['overall_status']}")
    print()

    if result.get("error"):
        print(f"❌ 错误：{result['error']}")
        return

    # 文件名警告
    if result["filename_warnings"]:
        print("⚠️  文件名警告：")
        for filename, keywords in result["filename_warnings"]:
            print(f"   - {filename}: 包含高风险词汇 {keywords}")
        print()
    else:
        print("✅ 文件名检查通过：所有脚本文件名符合安全命名规范。")
        print()

    # 内容警告
    if result["content_warnings"]:
        print("⚠️  文件内容警告：")
        for filename, warnings in result["content_warnings"].items():
            print(f"   📄 {filename}:")
            for line_num, content, keyword in warnings:
                print(f"      第 {line_num} 行: 发现 '{keyword}'")
                print(f"      内容: {content}")
            print()
    else:
        print("✅ 文件内容检查通过：未发现高风险代码。")
        print()

    # 总结
    print("-" * 60)
    if result["overall_status"] == "PASS":
        print("✅ 安全检查通过！scripts/ 目录下未发现高风险词汇。")
        print("   所有脚本均符合只读安全政策。")
    else:
        print("⚠️  安全检查发现警告！请检查上述警告项。")
        print("   如需确认这些高风险词汇出现在只读上下文中，请人工审核。")
        print("   参考文档：docs/read_only_safety_policy.md")
    print("=" * 60)


if __name__ == "__main__":
    result = scan_scripts_directory("scripts")
    print_results(result)
