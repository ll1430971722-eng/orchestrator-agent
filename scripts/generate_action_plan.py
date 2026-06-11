"""
行动清单生成脚本 [只读]

功能：
    读取 problem_diagnosis.md，生成可执行的人工行动清单。
    输出 output/reports/action_plan.md

安全声明：
    - 本脚本只生成人工执行建议，不自动执行任何店铺操作
    - 行动清单中的所有任务都需要人工判断后执行
    - Agent 不修改店铺任何数据
"""

import os
from datetime import datetime
from typing import List, Dict, Any


def load_diagnosis_report() -> str:
    """
    读取问题诊断报告。

    Returns:
        str: 诊断报告内容
    """
    report_path = "output/reports/problem_diagnosis.md"
    if not os.path.exists(report_path):
        return ""
    with open(report_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_problems(report_content: str) -> List[Dict[str, Any]]:
    """
    从诊断报告中解析问题列表。

    Args:
        report_content: 报告 Markdown 内容

    Returns:
        list: 解析后的问题字典列表
    """
    # TODO: 实现 Markdown 解析逻辑
    problems = []
    return problems


def generate_action_table(problems: List[Dict[str, Any]]) -> str:
    """
    生成行动清单表格。

    Args:
        problems: 问题列表

    Returns:
        str: 行动清单 Markdown 内容
    """
    lines = []
    lines.append("# 运营行动清单\n")
    lines.append(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**重要声明：** 以下所有任务都需要人工判断后执行。Agent 不会自动执行任何操作。\n")
    lines.append("---\n")

    if not problems:
        lines.append("\n当前无待处理问题。请先运行 diagnose_problems.py 生成诊断报告。\n")
    else:
        # 行动清单表格
        lines.append("\n## 行动清单\n")
        lines.append("| 序号 | 任务 | 对应问题 | 负责人 | 优先级 | 预计影响 | 执行难度 | 建议完成时间 | 需检查的数据 | 完成状态 |")
        lines.append("|------|------|----------|--------|--------|----------|----------|--------------|--------------|----------|")
        lines.append("| - | 待诊断报告数据填充 | - | - | - | - | - | - | - | ⬜ |")

        lines.append("\n## 新手优先级解释\n")
        lines.append("为什么先做这些任务：\n")
        lines.append("- 高优先级任务直接影响利润或店铺评分\n")
        lines.append("- 中优先级任务影响运营效率\n")
        lines.append("- 低优先级任务可以排期处理\n")

        lines.append("\n## 哪些任务可以晚点做\n")
        lines.append("- 不直接影响 GMV 或店铺评分的任务\n")
        lines.append("- 需要长时间观察才能判断效果的任务\n")
        lines.append("- 依赖其他任务完成后的数据反馈\n")

        lines.append("\n## 哪些任务不能盲目做\n")
        lines.append("- 原因未查清前不要大规模调整\n")
        lines.append("- 不要同时修改多个变量（无法归因效果）\n")
        lines.append("- 不要在数据不足时下结论\n")

        lines.append("\n## 做完以后看哪些数据反馈\n")
        lines.append("每个任务完成后，需要在对应时间窗口内观察以下指标：\n")
        lines.append("- **1-3 天：** 点击率、访问量变化\n")
        lines.append("- **3-7 天：** 转化率、GMV 变化\n")
        lines.append("- **7-14 天：** 退款率、店铺评分变化\n")

    lines.append(f"\n---\n")
    lines.append(f"*本清单由 douyin-shop-agent 生成，所有任务需人工执行。*\n")

    return "".join(lines)


def save_action_plan(content: str) -> str:
    """
    保存行动清单。

    Returns:
        str: 文件路径
    """
    report_dir = "output/reports"
    os.makedirs(report_dir, exist_ok=True)

    filepath = os.path.join(report_dir, "action_plan.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


if __name__ == "__main__":
    print("行动清单生成 [只读]")

    # 读取诊断报告
    report_content = load_diagnosis_report()
    if not report_content:
        print("⚠️  未找到诊断报告，请先运行 diagnose_problems.py")
        # 生成空模板
        problems = []
    else:
        problems = parse_problems(report_content)

    # 生成行动清单
    action_content = generate_action_table(problems)

    # 保存
    output_path = save_action_plan(action_content)
    print(f"行动清单已生成：{output_path}")
    print("安全声明：所有任务需人工判断后执行，Agent 不自动修改店铺。")
