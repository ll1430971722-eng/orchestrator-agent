"""
日报生成脚本 [只读]

功能：
    生成完整的日报模板。
    整合数据、诊断、行动清单和未来建议。

输出：
    - output/reports/daily_report_template.md

安全声明：
    - 本脚本只生成报告模板和建议，不自动执行任何店铺操作
"""

import os
from datetime import datetime
from typing import Dict, Any, List


def generate_daily_report(data: Dict[str, Any] = None) -> str:
    """
    生成日报 Markdown 内容。

    Args:
        data: 日数据（可选，为空时生成模板）

    Returns:
        str: 日报 Markdown 内容
    """
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append(f"# 📊 抖音店铺运营日报\n")
    lines.append(f"**日期：** {today}\n")
    lines.append(f"**生成时间：** {now}\n")
    lines.append(f"**重要声明：** 本报告中的所有建议均为人工执行建议，Agent 不会自动执行任何店铺修改。\n")
    lines.append("---\n")

    # ========== 1. 今日店铺概况 ==========
    lines.append("\n## 一、今日店铺概况\n")
    lines.append("> 用一句话概括今天店铺的整体状态。\n")
    lines.append("待数据填充后生成。\n")

    # ========== 2. 核心数据变化 ==========
    lines.append("\n## 二、核心数据变化\n")
    lines.append("| 指标 | 今日值 | 昨日值 | 环比变化 | 近7日均值 | 趋势 |")
    lines.append("|------|--------|--------|----------|-----------|------|")
    lines.append("| GMV | - | - | - | - | - |")
    lines.append("| 订单数 | - | - | - | - | - |")
    lines.append("| 退款率 | - | - | - | - | - |")
    lines.append("| 支付转化率 | - | - | - | - | - |")
    lines.append("| 客单价 | - | - | - | - | - |")
    lines.append("| 广告消耗 | - | - | - | - | - |")
    lines.append("| 广告 ROI | - | - | - | - | - |")

    # 数据完整性说明
    lines.append("\n**数据完整性：**\n")
    lines.append("- 订单数据：待接入\n")
    lines.append("- 商品数据：待接入\n")
    lines.append("- 流量数据：待接入\n")
    lines.append("- 广告数据：待接入\n")
    lines.append("- 售后数据：待接入\n")

    # ========== 3. 今日最重要的问题 ==========
    lines.append("\n## 三、今日最重要的问题\n")
    lines.append("详见 `problem_diagnosis.md`\n")

    # ========== 4. 每个问题的数据依据 ==========
    lines.append("\n## 四、数据依据\n")
    lines.append("> 每个问题都必须有明确的数据支撑。\n")
    lines.append("待诊断数据填充。\n")

    # ========== 5. 可能原因 ==========
    lines.append("\n## 五、可能原因分析\n")
    lines.append("> 按可能性从高到低排列，不做确定性断言。\n")
    lines.append("待诊断数据填充。\n")

    # ========== 6. 解决方案 ==========
    lines.append("\n## 六、解决方案\n")
    lines.append("> 每个方案包含：具体动作、负责人、预计完成时间、验证方法。\n")
    lines.append("详见 `action_plan.md`\n")

    # ========== 7. 今日必须做的 3 件事 ==========
    lines.append("\n## 七、今日必须做的 3 件事\n")
    lines.append("| 序号 | 任务 | 负责人 | 预计完成时间 |")
    lines.append("|------|------|--------|--------------|")
    for i in range(1, 4):
        lines.append(f"| {i} | 待数据填充 | - | - |")

    # ========== 8. 未来 3 天建议 ==========
    lines.append("\n## 八、未来 3 天建议\n")
    lines.append("详见 `future_recommendations.md`\n")

    # ========== 9. 未来 7 天观察重点 ==========
    lines.append("\n## 九、未来 7 天观察重点\n")
    lines.append("- 各项优化动作的效果数据\n")
    lines.append("- 被标记为「观察」的商品变化\n")
    lines.append("- 店铺评分和评价变化\n")

    # ========== 10. 未来 30 天运营方向 ==========
    lines.append("\n## 十、未来 30 天运营方向\n")
    lines.append("详见 `future_recommendations.md`\n")

    # ========== 11. 给运营新手的解释 ==========
    lines.append("\n## 十一、给运营新手的解释\n")
    lines.append("> 看不懂上面这些指标？这里是通俗解释：\n")
    lines.append("- **曝光**：有多少人看到你的商品——就像店门口路过的人数\n")
    lines.append("- **点击率**：看到后有多少人点进来——就像路过的人有多少进店了\n")
    lines.append("- **转化率**：进来后有多少人买了——就像进店的人有多少掏钱了\n")
    lines.append("- **退款率**：买了又退的比例——卖出去了但又被退回来\n")
    lines.append("- **ROI**：广告花的钱有没有赚回来——投入 1 元能赚回几元\n")
    lines.append("- **GMV**：成交总额——今天总共卖了多少钱的货\n")

    # ========== 12. 明天需要重点看的指标 ==========
    lines.append("\n## 十二、明天需要重点看的指标\n")
    lines.append("- [ ] 今日优化动作的初步数据反馈\n")
    lines.append("- [ ] 重点商品的点击率和转化率变化\n")
    lines.append("- [ ] 退款率是否有波动\n")
    lines.append("- [ ] 广告 ROI 是否在可接受范围内\n")

    lines.append(f"\n---\n")
    lines.append(f"*本日报由 douyin-shop-agent 自动生成。所有建议均为人工执行建议，Agent 不会自动执行任何店铺修改。*\n")

    return "".join(lines)


def save_report(content: str) -> str:
    """
    保存日报。

    Returns:
        str: 文件路径
    """
    report_dir = "output/reports"
    os.makedirs(report_dir, exist_ok=True)

    filepath = os.path.join(report_dir, "daily_report_template.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"日报生成 [只读] - {today}")

    report = generate_daily_report()
    output_path = save_report(report)

    print(f"日报模板已生成：{output_path}")
    print("安全声明：报告中所有建议均为人工执行建议。")
