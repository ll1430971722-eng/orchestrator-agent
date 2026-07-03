"""
运营问题诊断脚本 [只读]

功能：
    读取 data/processed/ 或 data/raw/ 下的指标数据，
    根据 metrics_rules 和 problem_solution_playbook 生成问题诊断报告。

诊断阈值来自 docs/metrics_rules.md，解决方案模板来自 docs/problem_solution_playbook.md

输入：
    - data/processed/daily_metrics_YYYY-MM-DD.json（优先）
    - 或 data/raw/YYYY-MM-DD/ 下的原始数据

输出：
    - output/reports/YYYY-MM-DD-diagnosis.md

安全声明：
    - 只读取本地数据，不做任何店铺修改
    - 诊断结果和建议均为人工执行建议，不自动执行操作
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import (
    DATA_PROCESSED, DATA_RAW, OUTPUT_REPORTS,
    THRESHOLD_GMV_DECLINE_HIGH, THRESHOLD_GMV_DECLINE_MEDIUM,
    THRESHOLD_REFUND_RATE_MULTIPLIER, THRESHOLD_REFUND_CONSECUTIVE_DAYS,
    THRESHOLD_CONVERSION_DECLINE, THRESHOLD_ROI_LOSS,
    THRESHOLD_ROI_DECLINE_DAYS, THRESHOLD_EXPOSURE_DECLINE,
    THRESHOLD_CLICK_RATE_DECLINE,
)

# ═══════════════════════════════════════════════════
# 数据加载
# ═══════════════════════════════════════════════════

def load_data(date: str) -> Dict[str, Any]:
    """加载已处理或原始数据。优先加载处理过的数据。"""
    processed_path = DATA_PROCESSED / f"daily_metrics_{date}.json"
    if processed_path.exists():
        with open(processed_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 回退到原始数据 + 实时计算
    from analyze_daily import load_raw_data, calculate_base_metrics
    raw = load_raw_data(date)
    return calculate_base_metrics(raw)


def load_historical_metrics(date: str, days: int = 7) -> List[Dict[str, Any]]:
    """加载历史指标数据"""
    end_date = datetime.strptime(date, "%Y-%m-%d")
    results = []
    for i in range(1, days + 1):
        d = (end_date - timedelta(days=i)).strftime("%Y-%m-%d")
        m = _load_single(d)
        if m:
            m["_date"] = d
            results.append(m)
    return results


def _load_single(date: str) -> Optional[Dict[str, Any]]:
    path = DATA_PROCESSED / f"daily_metrics_{date}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ═══════════════════════════════════════════════════
# 诊断引擎
# ═══════════════════════════════════════════════════

_PLAYBOOK = {
    "gmv_decline": {
        "title_template": "⚠️ GMV 异常下降",
        "possible_causes": [
            "内容发布减少或质量下降",
            "商品点击率下降（主图/标题吸引力减弱）",
            "店铺权重波动（评分、违规）",
            "主推商品吸引力下降或被竞品超越",
            "流量渠道结构变化（某一渠道衰减）",
        ],
        "solutions": [
            "人工检查最近 7 天流量来源变化，定位下降渠道",
            "如内容是主因：增加短视频发布频次，优化内容质量",
            "如主图/标题问题：优化主图和标题",
            "检查店铺评分、违规提醒、商品状态",
            "检查竞品是否有大动作",
        ],
        "priority": "高",
        "responsible_role": "运营",
        "verification_days": "3-7 天",
        "beginner_explanation": "流量下降说明进入店铺或商品的人变少了。先不要急着改价格，要先判断是曝光少了（平台没推），还是用户看到后不愿意点（主图/标题问题）。",
        "next_3_days": ["定位下降渠道", "检查店铺评分和违规"],
        "next_7_days": ["观察曝光和点击率趋势", "对比各渠道流量占比变化"],
        "next_30_days": ["建立每日内容发布节奏", "定期检查商品主图和标题效果"],
        "dont": ["不要一上来就降价", "不要同时大改多个商品（无法判断哪个动作有效）", "不要只看 GMV，不看流量来源"],
    },
    "refund_rate_high": {
        "title_template": "🔴 退款率异常升高",
        "possible_causes": [
            "商品描述和实际不一致（过度承诺）",
            "用户预期被营销拉高",
            "发货或物流体验差",
            "客服解释不到位",
            "某个商品本身售后风险高",
        ],
        "solutions": [
            "人工整理退款原因 TOP 5",
            "修改容易误导的详情页文案",
            "优化发货和包装流程",
            "给客服准备针对性的解释话术",
            "暂缓放大该商品投放",
        ],
        "priority": "高",
        "responsible_role": "运营",
        "verification_days": "3-7 天",
        "beginner_explanation": "订单上涨不一定是好事，如果退款率也上涨，说明成交质量可能不好。退款率高会影响利润（退款产生成本）和店铺评分（影响后续流量）。",
        "next_3_days": ["整理退款原因 TOP 5", "检查问题商品的详情页描述"],
        "next_7_days": ["观察退款率变化", "重点监控问题商品售后数据"],
        "next_30_days": ["建立退款原因周度分析机制", "新商品上线前进行描述准确性审核"],
        "dont": ["不要只看订单增长就高兴", "不要在退款原因没查清前继续加大投放"],
    },
    "conversion_low": {
        "title_template": "🟡 访问量高但转化率低",
        "possible_causes": [
            "详情页没有解决用户疑虑",
            "评价不足或差评影响信任",
            "价格阻力大",
            "优惠不明显",
            "客服响应慢或话术不专业",
        ],
        "solutions": [
            "人工优化详情页前 3 屏（首屏卖点、信任背书、价格理由）",
            "增加信任背书（评价引导、资质展示）",
            "优化客服话术和响应速度",
            "设置限时优惠或满减",
        ],
        "priority": "中",
        "responsible_role": "运营",
        "verification_days": "3-5 天",
        "beginner_explanation": "访问量高说明有人进来了，但没买。这个阶段要看用户为什么不敢下单。常见问题是详情页不清楚、评价少、价格觉得贵、客服没接住。",
        "next_3_days": ["检查详情页前3屏", "检查最新评价和问答"],
        "next_7_days": ["观察转化率变化", "如有改动，对比改动前后数据"],
        "next_30_days": ["持续积累好评和问答", "建立客服标准话术库"],
        "dont": ["不要只增加流量（来更多人但不解决转化，浪费流量）", "不要在转化没解决前盲目加广告预算"],
    },
    "ad_roi_low": {
        "title_template": "🔴 广告 ROI 亏损",
        "possible_causes": [
            "广告素材吸引力不足（点击率低）",
            "人群不精准（曝给了不对的人）",
            "商品转化差（点进去了但不买）",
            "出价或预算不合理",
            "投放计划学习效果差（新计划冷启动）",
        ],
        "solutions": [
            "人工检查低 ROI 计划，逐一排查",
            "对亏损计划：降低预算或暂停观察",
            "换广告素材测试",
            "检查落地商品转化能力",
            "优化人群定向",
        ],
        "priority": "高",
        "responsible_role": "投手",
        "verification_days": "2-3 天",
        "beginner_explanation": "ROI 是投入产出比。ROI < 1 说明在亏钱。ROI 低不要只怪投手，也要看商品本身能不能承接流量。",
        "next_3_days": ["暂停亏损计划", "换素材测试"],
        "next_7_days": ["观察新素材 ROI", "检查落地商品转化"],
        "next_30_days": ["建立广告效果周度复盘机制", "保持 3-5 套素材轮换测试"],
        "dont": ["不要在 ROI 低时盲目加预算", "不要只改投放，不看商品页面和转化"],
    },
    "exposure_decline": {
        "title_template": "⚠️ 曝光大幅下降",
        "possible_causes": [
            "平台推荐权重变化",
            "商品或店铺状态异常（违规、下架）",
            "内容发布断档",
            "搜索排名下降",
            "竞品抢占流量",
        ],
        "solutions": [
            "检查店铺评分、违规提醒、商品状态",
            "检查最近是否有内容发布空窗",
            "搜索核心关键词，检查排名变化",
            "分析各渠道曝光变化，定位下降渠道",
        ],
        "priority": "中",
        "responsible_role": "运营",
        "verification_days": "3-7 天",
        "beginner_explanation": "曝光下降说明平台没有把你的商品推给足够多的用户。先排查是不是店铺或商品本身出了问题（评分、违规），再考虑内容策略。",
        "next_3_days": ["检查店铺状态和评分", "排查各渠道曝光变化"],
        "next_7_days": ["增量发布内容", "观察曝光恢复情况"],
        "next_30_days": ["保持稳定内容发布节奏", "关注搜索排名"],
        "dont": ["不要在原因不明时大幅改价或加大投放", "不要只看一天数据就下结论"],
    },
    "product_sudden_decline": {
        "title_template": "🟡 单品突然下滑",
        "possible_causes": [
            "流量减少（曝光下降）",
            "主图/标题吸引力下降或过时",
            "库存不足或价格异常",
            "差评出现导致转化下降",
            "竞品上新品或做活动抢流量",
        ],
        "solutions": [
            "人工检查库存和价格是否正常",
            "检查是否有最新差评影响",
            "对比近 7 天数据，定位是流量/点击/转化哪个环节出问题",
            "临时补内容流量（短视频、直播）",
        ],
        "priority": "中",
        "responsible_role": "运营",
        "verification_days": "2-3 天",
        "beginner_explanation": "单品突然下滑不要急着乱改。先判断是流量问题（没人看）、点击问题（看了不点）、转化问题（点了不买）还是售后问题（买了又退）。",
        "next_3_days": ["定位下滑环节（流量/点击/转化/售后）", "检查库存和价格"],
        "next_7_days": ["根据定位结果针对性优化", "观察单品数据恢复"],
        "next_30_days": ["为核心商品建立数据监控", "定期检查竞品动态"],
        "dont": ["不要第一时间乱改所有内容", "不要只凭一天数据下结论", "不要在原因不明时直接降价或加广告"],
    },
}


def diagnose(data: Dict[str, Any], historical: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    根据数据诊断运营问题。

    诊断逻辑基于 docs/metrics_rules.md 的阈值定义：
    - GMV 日环比下降 > 30% → 高风险
    - GMV 日环比下降 15-30% → 中等风险
    - 退款率 > 行业均值 × 1.5 → 高风险
    - 支付转化率日环比下降 > 20% → 需要排查
    - ROI < 1 → 亏损
    - 曝光日环比下降 > 30% → 需要排查

    Args:
        data: 当日指标数据
        historical: 历史指标数据（用于趋势判断）

    Returns:
        list: 问题列表，按优先级排序（高→中）
    """
    problems = []

    # ── 1. GMV 异常检查 ──
    gmv_change = _safe_float(data.get("gmv_change_pct", 0))
    gmv = _safe_float(data.get("gmv", 0))

    if gmv_change < 0:
        if abs(gmv_change) > THRESHOLD_GMV_DECLINE_HIGH * 100:
            problems.append(_make_problem("gmv_decline", data, {
                "data_evidence": f"GMV 日环比下降 {abs(gmv_change):.1f}%（阈值 >{THRESHOLD_GMV_DECLINE_HIGH*100:.0f}%），当前 GMV ¥{gmv:,.2f}",
                "severity": "高",
            }))
        elif abs(gmv_change) > THRESHOLD_GMV_DECLINE_MEDIUM * 100:
            problems.append(_make_problem("gmv_decline", data, {
                "data_evidence": f"GMV 日环比下降 {abs(gmv_change):.1f}%（阈值 {THRESHOLD_GMV_DECLINE_MEDIUM*100:.0f}%-{THRESHOLD_GMV_DECLINE_HIGH*100:.0f}%），当前 GMV ¥{gmv:,.2f}",
                "severity": "中",
            }))

    # ── 2. 退款率异常检查 ──
    refund_rate = _safe_float(data.get("refund_rate", 0))
    refund_rate_change = _safe_float(data.get("refund_rate_change_pct", 0))

    if refund_rate > 20:  # 超过 20% 已经很严重
        problems.append(_make_problem("refund_rate_high", data, {
            "data_evidence": f"退款率 {refund_rate:.1f}%，远超健康线（通常 <10%）。退款金额 ¥{_safe_float(data.get('refund_amount', 0)):,.2f}",
            "severity": "高",
        }))
    elif refund_rate > 10:
        problems.append(_make_problem("refund_rate_high", data, {
            "data_evidence": f"退款率 {refund_rate:.1f}%，高于警戒线 10%。退款金额 ¥{_safe_float(data.get('refund_amount', 0)):,.2f}",
            "severity": "中",
        }))

    # 退款率连续上涨检查
    if historical and refund_rate_change > 0:
        consecutive_up = 1
        for h in sorted(historical, key=lambda x: x.get("_date", ""), reverse=True):
            h_change = _safe_float(h.get("refund_rate_change_pct", 0))
            if h_change > 0:
                consecutive_up += 1
            else:
                break
        if consecutive_up >= THRESHOLD_REFUND_CONSECUTIVE_DAYS:
            existing = [p for p in problems if p.get("_problem_type") == "refund_rate_high"]
            if not existing:  # 避免重复添加
                problems.append(_make_problem("refund_rate_high", data, {
                    "data_evidence": f"退款率连续 {consecutive_up} 天上涨（阈值: 连续{THRESHOLD_REFUND_CONSECUTIVE_DAYS}天），当前 {refund_rate:.1f}%",
                    "severity": "中",
                }))

    # ── 3. 转化率异常检查 ──
    conversion = _safe_float(data.get("click_conversion_rate", data.get("conversion_rate", 0)))
    conversion_change = _safe_float(data.get("click_conversion_rate_change_pct", data.get("conversion_rate_change_pct", 0)))

    if conversion_change < 0 and abs(conversion_change) > THRESHOLD_CONVERSION_DECLINE * 100:
        problems.append(_make_problem("conversion_low", data, {
            "data_evidence": f"点击→成交转化率日环比下降 {abs(conversion_change):.1f}%（阈值 >{THRESHOLD_CONVERSION_DECLINE*100:.0f}%），当前转化率 {conversion:.2f}%",
            "severity": "中",
        }))

    # 加购高但支付低
    add_to_cart = _safe_float(data.get("add_to_cart_rate", 0))
    if add_to_cart > 5 and conversion < 3:
        problems.append(_make_problem("conversion_low", data, {
            "data_evidence": f"加购率 {add_to_cart:.1f}% 正常但转化率仅 {conversion:.1f}%，疑似价格或信任问题（加购高但支付低）",
            "severity": "中",
        }))

    # ── 4. 广告 ROI 检查 ──
    ad_roi = _safe_float(data.get("ad_roi", -1))
    ad_spend = _safe_float(data.get("ad_spend", 0))

    if ad_roi >= 0 and ad_roi < THRESHOLD_ROI_LOSS and ad_spend > 0:
        problems.append(_make_problem("ad_roi_low", data, {
            "data_evidence": f"广告 ROI = {ad_roi:.2f}（<{THRESHOLD_ROI_LOSS}），处于亏损状态。广告消耗 ¥{ad_spend:,.2f}",
            "severity": "高",
        }))

    # ROI 连续下降检查
    if historical and ad_roi >= 0:
        consecutive_roi_down = 1
        prev_roi = ad_roi
        for h in sorted(historical, key=lambda x: x.get("_date", ""), reverse=True):
            h_roi = _safe_float(h.get("ad_roi", -1))
            if h_roi >= 0 and h_roi > prev_roi:
                consecutive_roi_down += 1
                prev_roi = h_roi
            else:
                break
        if consecutive_roi_down >= THRESHOLD_ROI_DECLINE_DAYS:
            existing = [p for p in problems if p.get("_problem_type") == "ad_roi_low"]
            if not existing:
                problems.append(_make_problem("ad_roi_low", data, {
                    "data_evidence": f"广告 ROI 连续 {consecutive_roi_down} 天下降（阈值: 连续{THRESHOLD_ROI_DECLINE_DAYS}天），当前 {ad_roi:.2f}",
                    "severity": "中",
                }))

    # ── 5. 流量异常检查 ──
    exposure_change = _safe_float(data.get("exposure_change_pct", 0))
    exposure = _safe_float(data.get("exposure", 0))
    click_rate_change = _safe_float(data.get("exposure_click_rate_change_pct", 0))

    if exposure_change < 0 and abs(exposure_change) > THRESHOLD_EXPOSURE_DECLINE * 100:
        problems.append(_make_problem("exposure_decline", data, {
            "data_evidence": f"曝光日环比下降 {abs(exposure_change):.1f}%（阈值 >{THRESHOLD_EXPOSURE_DECLINE*100:.0f}%），当前曝光 {exposure:,.0f}",
            "severity": "中",
        }))

    if click_rate_change < 0 and abs(click_rate_change) > THRESHOLD_CLICK_RATE_DECLINE * 100:
        problems.append(_make_problem("exposure_decline", data, {
            "data_evidence": f"点击率日环比下降 {abs(click_rate_change):.1f}%（阈值 >{THRESHOLD_CLICK_RATE_DECLINE*100:.0f}%），疑似主图或标题问题",
            "severity": "中",
        }))

    # ── 6. 单品异常检查 ──
    product_ranking = data.get("product_ranking", [])
    refund_ranking = data.get("refund_ranking", [])

    # 如果 TOP1 退款商品也出现在 GMV TOP 中，说明主力商品有售后问题
    if product_ranking and refund_ranking:
        top_gmv_names = {p["name"] for p in product_ranking[:3]}
        for r in refund_ranking[:3]:
            if r["name"] in top_gmv_names:
                problems.append(_make_problem("product_sudden_decline", data, {
                    "data_evidence": f"主力商品「{r['name']}」同时出现在 GMV TOP 和退款 TOP 中，退款金额 ¥{r['refund_amount']:,.2f}",
                    "severity": "中",
                }))
                break  # 只报一次

    # ── 7. 按优先级排序 ──
    priority_order = {"高": 0, "中": 1, "低": 2}
    problems.sort(key=lambda p: priority_order.get(p.get("priority", "中"), 1))

    return problems


def _make_problem(problem_type: str, data: Dict[str, Any], context: Dict[str, str]) -> Dict[str, Any]:
    """从 playbook 模板 + 上下文数据构造一个问题诊断结果"""
    pb = _PLAYBOOK.get(problem_type, _PLAYBOOK["gmv_decline"])
    return {
        "_problem_type": problem_type,
        "title": f"{context.get('severity', '中')}风险 - {pb['title_template']}",
        "data_evidence": context.get("data_evidence", ""),
        "possible_causes": pb["possible_causes"],
        "solutions": pb["solutions"],
        "priority": pb["priority"],
        "verification_method": f"优化后观察 {pb['verification_days']}",
        "expected_impact": "高" if pb["priority"] == "高" else "中",
        "execution_difficulty": "中",
        "responsible_role": pb["responsible_role"],
        "deadline_suggestion": "24小时内确认问题原因" if pb["priority"] == "高" else "3天内排查",
        "beginner_explanation": pb["beginner_explanation"],
        "next_3_days": pb["next_3_days"],
        "next_7_days": pb["next_7_days"],
        "next_30_days": pb["next_30_days"],
        "dont": pb.get("dont", []),
    }


def _safe_float(val: Any) -> float:
    """安全转 float，None 或非数字返回 0.0"""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


# ═══════════════════════════════════════════════════
# 报告生成
# ═══════════════════════════════════════════════════

def generate_diagnosis_report(problems: List[Dict[str, Any]], date: str) -> str:
    """生成 Markdown 格式的问题诊断报告"""
    OUTPUT_REPORTS.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append(f"# 运营问题诊断报告\n")
    lines.append(f"**日期：** {date}\n")
    lines.append(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**重要声明：** 本报告中的所有建议均为人工执行建议，Agent 不会自动执行任何店铺修改。\n")
    lines.append("---\n")

    if not problems:
        lines.append("\n## ✅ 未发现明显异常\n")
        lines.append("当前指标在正常范围内，继续保持。\n")
        lines.append("\n### 常规建议\n")
        lines.append("- 保持每日内容发布节奏\n")
        lines.append("- 定期检查商品主图和标题效果\n")
        lines.append("- 关注竞品动态\n")
    else:
        high_priority = [p for p in problems if p["priority"] == "高"]
        mid_priority = [p for p in problems if p["priority"] == "中"]

        lines.append(f"\n## 共发现 {len(problems)} 个问题（{len(high_priority)} 个高风险，{len(mid_priority)} 个中风险）\n")

        for i, problem in enumerate(problems, 1):
            severity_emoji = "🔴" if problem["priority"] == "高" else "🟡"
            lines.append(f"### 问题 {i}：{severity_emoji} {problem.get('title', '未命名问题')}\n")
            lines.append(f"- **数据依据：** {problem.get('data_evidence', '待补充')}\n")
            lines.append(f"- **可能原因（按可能性排序）：**\n")
            for cause in problem.get("possible_causes", []):
                lines.append(f"  1. {cause}\n" if cause == problem["possible_causes"][0] else f"  1. {cause}\n".replace("1.", f"  {problem['possible_causes'].index(cause)+1}."))
            # fix the numbering
            lines.pop()
            for j, cause in enumerate(problem.get("possible_causes", []), 1):
                lines.append(f"  {j}. {cause}\n")

            lines.append(f"- **建议验证方法：** {problem.get('verification_method', '待补充')}\n")
            lines.append(f"- **具体解决方案：**\n")
            for sol in problem.get("solutions", []):
                lines.append(f"  - {sol}\n")
            lines.append(f"- **优先级：** {problem.get('priority', '待评估')}\n")
            lines.append(f"- **预计影响：** {problem.get('expected_impact', '待评估')}\n")
            lines.append(f"- **执行难度：** {problem.get('execution_difficulty', '待评估')}\n")
            lines.append(f"- **建议负责人：** {problem.get('responsible_role', '运营')}\n")
            lines.append(f"- **截止时间建议：** {problem.get('deadline_suggestion', '待定')}\n")
            lines.append(f"\n**💡 新手解释：** {problem.get('beginner_explanation', '待补充')}\n")
            lines.append(f"\n**未来 3 天建议：**\n")
            for item in problem.get("next_3_days", []):
                lines.append(f"  - {item}\n")
            lines.append(f"\n**未来 7 天观察重点：**\n")
            for item in problem.get("next_7_days", []):
                lines.append(f"  - {item}\n")
            lines.append(f"\n**未来 30 天方向：**\n")
            for item in problem.get("next_30_days", []):
                lines.append(f"  - {item}\n")
            if problem.get("dont"):
                lines.append(f"\n**❌ 不推荐：**\n")
                for item in problem["dont"]:
                    lines.append(f"  - {item}\n")
            lines.append("\n---\n")

    lines.append(f"\n*报告由 orchestrator-agent 自动生成，所有建议均为人工执行建议。*\n")

    report_path = OUTPUT_REPORTS / f"{date}-diagnosis.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return str(report_path)


# ═══════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"🔍 运营问题诊断 [只读] - {today}\n")

    # 加载数据
    data = load_data(today)

    # 加载历史数据用于趋势判断
    historical = load_historical_metrics(today, days=7)

    # 诊断
    problems = diagnose(data, historical)

    # 生成报告
    report_path = generate_diagnosis_report(problems, today)

    # 输出摘要
    high = [p for p in problems if p["priority"] == "高"]
    mid = [p for p in problems if p["priority"] == "中"]

    print(f"发现 {len(problems)} 个问题:")
    for i, p in enumerate(problems, 1):
        print(f"  {i}. [{p['priority']}] {p['title']}")

    print(f"\n📄 报告已生成: {report_path}")
    print(f"   高风险: {len(high)} | 中风险: {len(mid)}")
    print("安全声明：所有建议均为人工执行建议，Agent 不自动修改店铺。")
