"""
运营问题诊断脚本 [只读]

功能：
    读取 data/processed/ 或 data/raw/ 下的数据，
    根据 metrics_rules 和 problem_solution_playbook 生成问题诊断报告。

输入：
    - data/processed/daily_metrics_YYYY-MM-DD.json
    - 或 data/raw/YYYY-MM-DD/ 下的原始数据

输出：
    - output/reports/problem_diagnosis.md

安全声明：
    - 只读取本地数据，不做任何店铺修改
    - 诊断结果和建议都是人工执行建议，不是自动操作
"""

import os
from datetime import datetime
from typing import List, Dict, Any


def load_data(date: str) -> Dict[str, Any]:
    """
    加载已处理或原始数据。
    """
    # 优先加载处理过的数据
    processed_path = f"data/processed/daily_metrics_{date}.json"
    if os.path.exists(processed_path):
        import json
        with open(processed_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 回退到原始数据
    from analyze_daily import load_raw_data, calculate_base_metrics
    raw = load_raw_data(date)
    return calculate_base_metrics(raw)


def diagnose(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    根据数据诊断运营问题。

    诊断逻辑基于 docs/metrics_rules.md 和 docs/problem_solution_playbook.md

    Args:
        data: 指标数据

    Returns:
        list: 问题列表，按优先级排序
    """
    problems = []

    # TODO: 实现真实的诊断逻辑
    # 1. 检查 GMV 是否异常下降
    # 2. 检查退款率是否异常
    # 3. 检查转化率是否异常
    # 4. 检查广告 ROI 是否异常
    # 5. 检查流量是否异常
    # 6. 检查单品是否异常
    # 7. 按优先级排序（高→中→低）

    # 每个问题的结构
    problem_template = {
        "title": "",                # 问题标题
        "data_evidence": "",        # 数据依据
        "possible_causes": [],      # 可能原因（按可能性排序）
        "verification_method": "",  # 建议验证方法
        "solutions": [],            # 具体解决方案
        "priority": "",             # 高/中/低
        "expected_impact": "",      # 预计影响：高/中/低
        "execution_difficulty": "", # 执行难度：高/中/低
        "responsible_role": "",     # 建议负责人：运营/美工/客服/主播/老板/投手
        "deadline_suggestion": "",  # 截止时间建议
        "beginner_explanation": "", # 给运营新手的解释
        "next_3_days": [],          # 未来 3 天建议
        "next_7_days": [],          # 未来 7 天观察重点
        "next_30_days": [],         # 未来 30 天方向
    }

    return problems


def generate_diagnosis_report(problems: List[Dict[str, Any]], date: str) -> str:
    """
    生成 Markdown 格式的问题诊断报告。

    Args:
        problems: 问题列表
        date: 日期

    Returns:
        str: 报告文件路径
    """
    report_lines = []
    report_lines.append(f"# 运营问题诊断报告\n")
    report_lines.append(f"**日期：** {date}\n")
    report_lines.append(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report_lines.append(f"**重要声明：** 本报告中的所有建议均为人工执行建议，Agent 不会自动执行任何店铺修改。\n")
    report_lines.append("---\n")

    if not problems:
        report_lines.append("\n## 今日概览\n")
        report_lines.append("当前无可诊断数据。请确保 data/raw/ 或 data/processed/ 下有可用数据。\n")
        report_lines.append("\n## 数据不足提示\n")
        report_lines.append("如果数据文件存在但仍显示此提示，请检查：\n")
        report_lines.append("1. 数据文件格式是否正确（JSON）\n")
        report_lines.append("2. 数据文件是否为空\n")
        report_lines.append("3. 数据字段是否匹配分析脚本预期\n")
    else:
        report_lines.append(f"\n## 今日最重要的 {min(3, len(problems))} 个问题\n\n")

        for i, problem in enumerate(problems, 1):
            report_lines.append(f"### 问题 {i}：{problem.get('title', '未命名问题')}\n")
            report_lines.append(f"- **数据依据：** {problem.get('data_evidence', '待补充')}\n")
            report_lines.append(f"- **可能原因：**\n")
            for cause in problem.get('possible_causes', []):
                report_lines.append(f"  - {cause}\n")
            report_lines.append(f"- **建议验证方法：** {problem.get('verification_method', '待补充')}\n")
            report_lines.append(f"- **具体解决方案：**\n")
            for sol in problem.get('solutions', []):
                report_lines.append(f"  - {sol}\n")
            report_lines.append(f"- **优先级：** {problem.get('priority', '待评估')}\n")
            report_lines.append(f"- **预计影响：** {problem.get('expected_impact', '待评估')}\n")
            report_lines.append(f"- **执行难度：** {problem.get('execution_difficulty', '待评估')}\n")
            report_lines.append(f"- **建议负责人：** {problem.get('responsible_role', '运营')}\n")
            report_lines.append(f"- **截止时间建议：** {problem.get('deadline_suggestion', '待定')}\n")
            report_lines.append(f"\n**💡 新手解释：** {problem.get('beginner_explanation', '待补充')}\n")
            report_lines.append(f"\n**未来 3 天建议：**\n")
            for item in problem.get('next_3_days', []):
                report_lines.append(f"  - {item}\n")
            report_lines.append(f"\n**未来 7 天观察重点：**\n")
            for item in problem.get('next_7_days', []):
                report_lines.append(f"  - {item}\n")
            report_lines.append(f"\n**未来 30 天方向：**\n")
            for item in problem.get('next_30_days', []):
                report_lines.append(f"  - {item}\n")
            report_lines.append("\n---\n")

    report_lines.append(f"\n*报告由 douyin-shop-agent 自动生成，所有建议均为人工执行建议。*\n")

    report_dir = "output/reports"
    os.makedirs(report_dir, exist_ok=True)

    report_path = os.path.join(report_dir, "problem_diagnosis.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines(report_lines)

    return report_path


if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"运营问题诊断 [只读] - {today}")

    # 加载数据
    data = load_data(today)

    # 诊断问题
    problems = diagnose(data)

    # 生成报告
    report_path = generate_diagnosis_report(problems, today)
    print(f"诊断报告已生成：{report_path}")
    print(f"发现 {len(problems)} 个问题")
    print("安全声明：所有建议均为人工执行建议，Agent 不自动修改店铺。")
