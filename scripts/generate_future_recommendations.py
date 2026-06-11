"""
未来运营建议生成脚本 [只读]

功能：
    读取 problem_diagnosis.md 或日报数据，生成未来运营建议。
    输出 output/reports/future_recommendations.md

安全声明：
    - 本脚本只生成建议，不自动执行任何店铺操作
    - 所有建议都是方向性指导，具体执行需人工判断
"""

import os
from datetime import datetime
from typing import List, Dict, Any


def load_data():
    """加载诊断报告和相关数据。"""
    # TODO: 从文件加载数据
    pass


def generate_future_recommendations(problems: List[Dict] = None) -> str:
    """
    生成未来运营建议报告。

    Args:
        problems: 问题列表（可选）

    Returns:
        str: 报告的 Markdown 内容
    """
    lines = []
    lines.append("# 未来运营建议\n")
    lines.append(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**重要声明：** 以下所有建议均为运营方向指导，需要人工判断后执行。Agent 不会自动执行任何操作。\n")
    lines.append("---\n")

    # ========== 1. 今日必须处理的 3 件事 ==========
    lines.append("\n## 一、今日必须处理的 3 件事\n")
    lines.append("> 这些是影响当天运营效果的最紧急事项。\n")

    for i in range(1, 4):
        lines.append(f"### 任务 {i}\n")
        lines.append(f"- **任务：** 待诊断报告数据填充\n")
        lines.append(f"- **为什么重要：** 待分析\n")
        lines.append(f"- **怎么做：** 待给出具体步骤\n")
        lines.append(f"- **谁负责：** 待指定\n")
        lines.append(f"- **今天完成到什么程度：** 待明确\n\n")

    # ========== 2. 未来 3 天建议 ==========
    lines.append("---\n")
    lines.append("\n## 二、未来 3 天建议\n")
    lines.append("> 这些是本周内可以完成、能够快速看到效果的动作。\n")

    lines.append("| 建议动作 | 目标指标 | 预期效果 | 观察方法 |")
    lines.append("|----------|----------|----------|----------|")
    lines.append("| 待数据填充 | - | - | - |")

    # ========== 3. 未来 7 天建议 ==========
    lines.append("\n---\n")
    lines.append("\n## 三、未来 7 天建议\n")
    lines.append("> 本周需要重点关注的运营事项。\n")

    lines.append("### 本周重点\n")
    lines.append("- 待根据数据确定本周核心关注指标\n")

    lines.append("### 哪些商品继续观察\n")
    lines.append("- 待根据单品数据列出需要观察的商品\n")

    lines.append("### 哪些问题不要急着下结论\n")
    lines.append("- 新上架商品的数据需要 1-2 周观察期\n")
    lines.append("- 单日数据波动不一定是趋势，需要看 3-7 天走势\n")
    lines.append("- 活动期间的数据不具代表性，需要活动后对比\n")

    lines.append("### 哪些内容/商品可以加推\n")
    lines.append("- 转化率高于店铺均值且稳定的商品\n")
    lines.append("- 退货率低于店铺均值的商品\n")
    lines.append("- 近 7 天数据稳步上升的内容\n")

    # ========== 4. 未来 30 天方向 ==========
    lines.append("\n---\n")
    lines.append("\n## 四、未来 30 天运营方向\n")
    lines.append("> 月度运营战略方向，帮助建立长期健康运营节奏。\n")

    lines.append("### 店铺目前最大的机会\n")
    lines.append("- 待分析后确定\n")

    lines.append("### 最大的风险\n")
    lines.append("- 待分析后确定\n")

    lines.append("### 应该培养的能力\n")
    lines.append("- 数据解读能力：学会看懂核心指标的含义和趋势\n")
    lines.append("- 内容生产能力：稳定的短视频发布节奏\n")
    lines.append("- 客服专业度：标准化的售前咨询和售后处理\n")
    lines.append("- 广告投放判断力：知道什么时候加、什么时候减\n")

    lines.append("### 应该建立的数据习惯\n")
    lines.append("- 每天看一次核心指标：GMV、订单数、退款率、广告 ROI\n")
    lines.append("- 每周做一次商品分析：哪个商品好、哪个商品差\n")
    lines.append("- 每次改完后记录：改了什么、哪天改的、效果怎样\n")
    lines.append("- 每月做一次竞品分析：看看同行在做什么\n")

    lines.append("### 各模块改进方向\n")
    lines.append("| 模块 | 改进方向 | 优先级 |")
    lines.append("|------|----------|--------|")
    lines.append("| 内容 | 建立稳定发布节奏，提升内容质量 | 待定 |")
    lines.append("| 商品 | 优化主图和详情页，积累好评 | 待定 |")
    lines.append("| 客服 | 标准化话术，提升响应速度 | 待定 |")
    lines.append("| 广告 | 控制 ROI 底线，优化素材和人群 | 待定 |")

    # ========== 5. 运营新手解释区 ==========
    lines.append("\n---\n")
    lines.append("\n## 五、运营新手解释区\n")
    lines.append("> 用简单语言解释本次报告中出现的核心运营概念。\n")

    beginner_concepts = {
        "曝光": "有多少人看到你的商品或内容。平台把你的东西展示给别人看的次数。",
        "点击率": "看到后有多少人愿意点进来。比如 100 人看到，3 人点进来，点击率就是 3%。",
        "转化率": "进店后有多少人真正下单买了。反映你的商品详情页和价格有没有说服力。",
        "客单价": "每个订单平均多少钱。GMV 除以订单数。",
        "退款率": "成交后又退掉的比例。退款率 = 退款订单数 / 总订单数。",
        "ROI": "投入产出比。ROI = 广告带来的成交金额 / 广告花费。ROI > 1 才赚钱。",
        "加购率": "访问商品的人中有多少人把商品加入了购物车。反映「心动了」的比例。",
    }

    for concept, explanation in beginner_concepts.items():
        lines.append(f"### {concept}\n")
        lines.append(f"{explanation}\n\n")

    lines.append(f"\n---\n")
    lines.append(f"*本报告由 douyin-shop-agent 生成。所有建议需人工判断后执行，Agent 不自动修改店铺。*\n")

    return "".join(lines)


def save_future_recommendations(content: str) -> str:
    """
    保存未来建议报告。

    Returns:
        str: 文件路径
    """
    report_dir = "output/reports"
    os.makedirs(report_dir, exist_ok=True)

    filepath = os.path.join(report_dir, "future_recommendations.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


if __name__ == "__main__":
    print("未来运营建议生成 [只读]")

    content = generate_future_recommendations()

    output_path = save_future_recommendations(content)
    print(f"未来运营建议已生成：{output_path}")
    print("安全声明：所有建议均为方向性指导，需人工判断后执行。")
