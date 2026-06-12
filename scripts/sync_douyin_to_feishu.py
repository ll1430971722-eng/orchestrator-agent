#!/usr/bin/env python3
"""
解析 douyin 日报，同步结构化数据到飞书多维表格

用法:
  python scripts/sync_douyin_to_feishu.py 2026-06-10
  python scripts/sync_douyin_to_feishu.py              # 默认今天
"""
import sys
import os
import re
from pathlib import Path
from datetime import datetime
import json

ORCHESTRATOR_ROOT = Path(__file__).resolve().parent.parent
FEISHU_MCP = ORCHESTRATOR_ROOT / "mcp-servers" / "feishu"
sys.path.insert(0, str(FEISHU_MCP))

from feishu_client import get_client, FeishuAPIError

# ── Constants ──
APP_TOKEN = "GPFtbIOhCafB4HsANmVcbFOan4f"
DAILY_METRICS_TABLE_ID = "tblK15Duu70dPX6G"
PROBLEM_TRACKING_TABLE_ID = "tblOZGoovyt8qb0I"
ACTION_TABLE_ID = "tblPj7sBL74M07dN"

DOUYIN_REPORTS = ORCHESTRATOR_ROOT / "output" / "reports"


# ═══════════════════════════════════════════════════
# 解析 douyin 日报
# ═══════════════════════════════════════════════════

def parse_number(text: str) -> float:
    """从文本中提取数字，去掉 ¥ % 单 人 ** 等"""
    text = str(text).strip()
    # 去掉加粗标记
    text = text.replace('**', '')
    # 去掉常见符号
    for ch in ['¥', '%', '单', '人', ',', '，', '~', '↑', '↓', '🟢', '🟡', '🔴', '⚠️', '✅', '<', '>']:
        text = text.replace(ch, '')
    text = text.strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def parse_change_pct(text: str) -> float:
    """解析变化百分比，如 '+78.03% ↑' → 78.03, '持平' → 0"""
    text = str(text).strip()
    if '持平' in text:
        return 0.0
    m = re.search(r'([+-]?\d+\.?\d*)', text)
    return float(m.group(1)) if m else 0.0


def parse_daily_metrics(date_str: str) -> dict:
    """解析 douyin daily_report 为结构化指标"""
    filepath = DOUYIN_REPORTS / f"daily_report_{date_str}.md"
    if not filepath.exists():
        print(f"❌ 日报不存在: {filepath}")
        return None

    content = filepath.read_text(encoding="utf-8")

    # ── 核心指标表格 ──
    # 找到 "## 一、核心指标" 后面的表格
    metrics = _parse_metrics_table(content)

    # ── 店铺评分 ──
    score_match = re.search(r'店铺评分.*?(\d+)\s*分.*?商品\s*(\d+).*?物流\s*(\d+).*?服务\s*(\d+)', content)
    store_score = int(score_match.group(1)) if score_match else 0
    product_score = int(score_match.group(2)) if score_match else 0
    logistics_score = int(score_match.group(3)) if score_match else 0
    service_score = int(score_match.group(4)) if score_match else 0

    # ── 漏斗 ──
    funnel = ""
    funnel_match = re.search(r'## 二、数据漏斗分析\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if funnel_match:
        funnel = funnel_match.group(1).strip()

    # ── 一句话总结 ──
    one_liner = ""
    oneliner_match = re.search(r'## 一句话总结\n\n\*\*(.+?)\*\*', content)
    if oneliner_match:
        one_liner = oneliner_match.group(1).strip()

    # ── 各渠道表现 ──
    channels = _parse_channel_table(content)

    # ── 售后 ──
    after_sales = _parse_after_sales(content)

    # ── 商品健康度 ──
    product_health = _parse_product_health(content)

    # ── 退款详情 ──
    refund_details = _parse_refund_details(content)

    # ── 明日关注 ──
    tomorrow = ""
    tm_match = re.search(r'## 七、明日关注\n\n(.*?)(?=\n##|\n---|\Z)', content, re.DOTALL)
    if tm_match:
        tomorrow = tm_match.group(1).strip()

    # ── 渠道亮点文本 ──
    channel_highlight = ""
    ch_match = re.search(r'## 四、各渠道表现.*?\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if ch_match:
        channel_highlight = ch_match.group(1).strip()

    return {
        "日期": date_str,
        "GMV（元）": metrics.get("gmv", 0),
        "GMV较昨日变化（%）": metrics.get("gmv_change", 0),
        "订单数": metrics.get("orders", 0),
        "订单数较昨日变化（%）": metrics.get("orders_change", 0),
        "客单价（元）": metrics.get("asp", 0),
        "客单价较昨日变化（%）": metrics.get("asp_change", 0),
        "同行客单价基准（元）": metrics.get("asp_peer", 0),
        "曝光人数": metrics.get("exposure", 0),
        "曝光较昨日变化（%）": metrics.get("exposure_change", 0),
        "曝光-点击率（%）": metrics.get("exposure_click_rate", 0),
        "曝光-点击率较昨日变化（%）": metrics.get("exposure_click_rate_change", 0),
        "同行曝光-点击率标杆（%）": metrics.get("exposure_click_rate_peer", 0),
        "点击-成交转化率（%）": metrics.get("click_conversion_rate", 0),
        "点击-成交转化率较昨日变化（%）": metrics.get("click_conversion_rate_change", 0),
        "同行点击-成交率基准（%）": metrics.get("click_conversion_rate_peer", 0),
        "成交人数": metrics.get("buyers", 0),
        "同行成交人数基准": metrics.get("buyers_peer", 0),
        "广告消耗（元）": metrics.get("ad_spend", 0),
        "退款率-支付口径（%）": metrics.get("refund_rate", 0),
        "退款率较昨日变化（%）": metrics.get("refund_rate_change", 0),
        "退款金额-退款口径（元）": refund_details.get("refund_amount_today", 0),
        "退款订单数": refund_details.get("refund_orders_today", 0),
        "7日累计退款金额（元）": refund_details.get("refund_7d_amount", 0),
        "7日累计退款率（%）": refund_details.get("refund_7d_rate", 0),
        "退款原因TOP1": refund_details.get("refund_reason_top1", ""),
        "退款原因TOP1占比（%）": refund_details.get("refund_reason_top1_pct", 0),
        "退款原因TOP2": refund_details.get("refund_reason_top2", ""),
        "退款原因TOP2占比（%）": refund_details.get("refund_reason_top2_pct", 0),
        # 渠道
        "搜索GMV（元）": channels.get("search_gmv", 0),
        "搜索GMV占比（%）": channels.get("search_pct", 0),
        "搜索环比（%）": channels.get("search_change", 0),
        "精选联盟GMV（元）": channels.get("affiliate_gmv", 0),
        "精选联盟GMV占比（%）": channels.get("affiliate_pct", 0),
        "精选联盟环比（%）": channels.get("affiliate_change", 0),
        "短视频GMV（元）": channels.get("video_gmv", 0),
        "短视频GMV占比（%）": channels.get("video_pct", 0),
        "短视频环比（%）": channels.get("video_change", 0),
        "商城GMV（元）": channels.get("mall_gmv", 0),
        "商城GMV占比（%）": channels.get("mall_pct", 0),
        # 评分
        "店铺总评分": store_score,
        "商品体验分": product_score,
        "物流体验分": logistics_score,
        "服务体验分": service_score,
        # 商品健康度
        "优秀商品数": product_health.get("excellent", 0),
        "有销量商品数": product_health.get("has_sales", 0),
        "零销量商品数": product_health.get("zero_sales", 0),
        "待发货订单数": after_sales.get("pending_ship", 0),
        "待处理售后数": after_sales.get("pending_after_sales", 0),
        # 总结文本
        "一句话总结": _clean_markdown(one_liner, max_len=300),
        "漏斗概况": _clean_markdown(funnel, max_len=400),
        "渠道亮点": _clean_markdown(channel_highlight, max_len=500),
        "明日关注": _clean_markdown(tomorrow, max_len=400),
    }


def _parse_metrics_table(content: str) -> dict:
    """解析核心指标表格"""
    result = {}

    # 找到表格区域
    table_match = re.search(r'## 一、核心指标\n\n(.*?)(?=\n\n##|\n\*\*)', content, re.DOTALL)
    if not table_match:
        table_match = re.search(r'## 一、核心指标\n\n\|.*?\|.*?\|.*?\|(.*?)(?=\n\n\*\*店铺评分|\n\n##)', content, re.DOTALL)
    if not table_match:
        return result

    table_text = table_match.group(0)

    # 逐行匹配: | 指标名 | 今日值 | 较昨日 | 同行基准 | 评价 |
    rows = re.findall(r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', table_text)

    for row in rows:
        indicator = row[0].strip()
        today_val = row[1].strip()
        change_val = row[2].strip()
        peer_val = row[3].strip()

        # GMV
        if '成交金额' in indicator or 'GMV' in indicator:
            result["gmv"] = parse_number(today_val)
            result["gmv_change"] = parse_change_pct(change_val)
        # 订单数
        elif '订单数' in indicator or '成交订单' in indicator:
            result["orders"] = int(parse_number(today_val))
            result["orders_change"] = parse_change_pct(change_val)
            if peer_val and peer_val != '-':
                result["orders_peer"] = int(parse_number(peer_val))
        # 客单价
        elif '客单价' in indicator:
            result["asp"] = parse_number(today_val)
            result["asp_change"] = parse_change_pct(change_val)
            if peer_val and peer_val != '-':
                result["asp_peer"] = parse_number(peer_val)
        # 退款率
        elif '退款率' in indicator and '支付' in indicator:
            result["refund_rate"] = parse_number(today_val)
            result["refund_rate_change"] = parse_change_pct(change_val)
        # 退款金额
        elif '退款金额' in indicator and '退款时间' in indicator:
            result["refund_amount"] = parse_number(today_val)
        # 曝光人数
        elif '曝光人数' in indicator or '商品曝光' in indicator:
            result["exposure"] = int(parse_number(today_val))
            result["exposure_change"] = parse_change_pct(change_val)
        # 曝光-点击率
        elif '曝光-点击' in indicator or '曝光点击' in indicator:
            result["exposure_click_rate"] = parse_number(today_val)
            result["exposure_click_rate_change"] = parse_change_pct(change_val)
            if peer_val and peer_val != '-':
                result["exposure_click_rate_peer"] = parse_number(peer_val)
        # 点击-成交转化率
        elif '点击-成交' in indicator or '点击成交' in indicator:
            result["click_conversion_rate"] = parse_number(today_val)
            result["click_conversion_rate_change"] = parse_change_pct(change_val)
            if peer_val and peer_val != '-':
                result["click_conversion_rate_peer"] = parse_number(peer_val)
        # 成交人数
        elif '成交人数' in indicator:
            result["buyers"] = int(parse_number(today_val))
            if peer_val and peer_val != '-':
                result["buyers_peer"] = int(parse_number(peer_val))
        # 广告消耗
        elif '广告消耗' in indicator or '广告投放' in indicator:
            result["ad_spend"] = parse_number(today_val)

    return result


def _parse_channel_table(content: str) -> dict:
    """解析渠道表现表格"""
    result = {}
    table_match = re.search(r'## 四、各渠道表现.*?\n\n\|.*?\|.*?\|.*?\|.*?\|\n(.*?)(?=\n\n|\n\*\*)', content, re.DOTALL)
    if not table_match:
        return result

    table_text = table_match.group(0)
    rows = re.findall(r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', table_text)

    for row in rows:
        channel = row[0].strip()
        gmv_str = row[1].strip()
        pct_str = row[2].strip()
        change_str = row[3].strip()

        if '搜索' in channel:
            result["search_gmv"] = parse_number(gmv_str)
            result["search_pct"] = parse_number(pct_str)
            result["search_change"] = parse_change_pct(change_str)
        elif '精选联盟' in channel or '达人' in channel:
            result["affiliate_gmv"] = parse_number(gmv_str)
            result["affiliate_pct"] = parse_number(pct_str)
            result["affiliate_change"] = parse_change_pct(change_str)
        elif '短视频' in channel:
            result["video_gmv"] = parse_number(gmv_str)
            result["video_pct"] = parse_number(pct_str)
            result["video_change"] = parse_change_pct(change_str)
        elif '商城' in channel:
            result["mall_gmv"] = parse_number(gmv_str)
            result["mall_pct"] = parse_number(pct_str)

    return result


def _parse_after_sales(content: str) -> dict:
    """解析售后数据"""
    result = {}

    # 待发货
    m = re.search(r'待发货.*?(\d+)\s*单', content)
    if m: result["pending_ship"] = int(m.group(1))

    # 待处理售后
    m = re.search(r'待处理售后.*?(\d+)\s*单', content)
    if m: result["pending_after_sales"] = int(m.group(1))

    return result


def _parse_product_health(content: str) -> dict:
    """解析商品健康度"""
    result = {}

    m = re.search(r'优秀商品.*?(\d+)\s*个', content)
    if m: result["excellent"] = int(m.group(1))

    m = re.search(r'有销量商品.*?(\d+)\s*个', content)
    if m: result["has_sales"] = int(m.group(1))

    m = re.search(r'零销量商品.*?(\d+)\s*个', content)
    if m: result["zero_sales"] = int(m.group(1))

    return result


def _parse_refund_details(content: str) -> dict:
    """解析退款详细数据（同时读日报和诊断报告）"""
    result = {}

    # 7日累计退款
    m = re.search(r'7\s*天累计退款.*?¥([\d,.]+)', content)
    if m: result["refund_7d_amount"] = parse_number(m.group(1))

    m = re.search(r'7\s*天累计退款.*?退款率\s*([\d.]+)%', content)
    if not m:
        m = re.search(r'7\s*日累计退款率.*?([\d.]+)%', content)
    if m: result["refund_7d_rate"] = float(m.group(1))

    # 今日退款金额（退款时间口径）
    m = re.search(r'今日退款金额.*?退款时间.*?¥([\d,.]+)', content)
    if m: result["refund_amount_today"] = parse_number(m.group(1))

    # 今日退款订单数
    m = re.search(r'今日退款订单数.*?退款时间.*?(\d+)\s*单', content)
    if m: result["refund_orders_today"] = int(m.group(1))

    # 退款原因
    # TOP原因：不再需要（61%）、冲动消费（9%）、竞品对比（4%）
    reason_match = re.search(r'TOP\s*原因[：:]\s*(.+?)(?:\n|$)', content)
    if reason_match:
        reasons_text = reason_match.group(1)
        # 解析 "不再需要（61%）、冲动消费（9%）、竞品对比（4%）"
        items = re.findall(r'(.+?)（([\d.]+)%）', reasons_text)
        if len(items) >= 1:
            result["refund_reason_top1"] = items[0][0].strip()
            result["refund_reason_top1_pct"] = float(items[0][1])
        if len(items) >= 2:
            result["refund_reason_top2"] = items[1][0].strip()
            result["refund_reason_top2_pct"] = float(items[1][1])

    return result


# ═══════════════════════════════════════════════════
# Markdown 清洗 → 飞书纯文本
# ═══════════════════════════════════════════════════

def _clean_markdown(text: str, max_len: int = 800) -> str:
    """把 markdown 清洗成飞书单元格可读的纯文本"""
    if not text:
        return ""

    lines = text.splitlines()
    clean_lines = []
    in_table = False

    for line in lines:
        stripped = line.strip()

        # 跳过空行和纯分隔符
        if not stripped or stripped in ['---', '---', '***']:
            if clean_lines and clean_lines[-1] != '':
                clean_lines.append('')
            continue

        # 跳过 markdown 表格分隔行
        if re.match(r'^\|[\s\-:|]+\|$', stripped):
            in_table = True
            continue

        # markdown 表格行 → 转为可读格式
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            # 去掉纯 emoji 或空单元格
            cells = [c for c in cells if c and not re.match(r'^[🟢🟡🔴⚠️✅]+$', c)]
            if cells:
                clean_lines.append(' · '.join(cells))
            in_table = True
            continue

        in_table = False

        # ### 标题 → 加【】标记
        if stripped.startswith('### '):
            clean_lines.append(f"【{stripped[4:].strip()}】")
            continue

        # ## 标题
        if stripped.startswith('## '):
            clean_lines.append(f"▎{stripped[3:].strip()}")
            continue

        # > 引用
        if stripped.startswith('> '):
            clean_lines.append(stripped[2:].strip())
            continue

        # 列表项
        if re.match(r'^[\-\*]\s+', stripped):
            clean_lines.append(f"• {stripped[2:].strip()}")
            continue

        # 数字列表
        if re.match(r'^\d+[\.\)]\s+', stripped):
            clean_lines.append(stripped)
            continue

        # 普通行
        clean_lines.append(stripped)

    # 合并，压缩多余空行
    result = '\n'.join(clean_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)

    # 去掉残留的 markdown 格式符号
    result = result.replace('**', '')
    result = result.replace('__', '')
    result = result.replace('`', '')

    # 截断（尽量在句号或换行处断开）
    if len(result) > max_len:
        result = result[:max_len]
        last_break = max(result.rfind('。'), result.rfind('\n'), result.rfind('.'))
        if last_break > max_len // 2:
            result = result[:last_break + 1]
        result = result.strip()

    return result


# ═══════════════════════════════════════════════════
# 解析问题诊断
# ═══════════════════════════════════════════════════

def parse_problems(date_str: str) -> tuple:
    """解析 problem_diagnosis 为 (问题列表, 行动建议列表)"""
    filepath = DOUYIN_REPORTS / f"problem_diagnosis_{date_str}.md"
    if not filepath.exists():
        print(f"⚠️ 诊断报告不存在: {filepath}")
        return [], []

    content = filepath.read_text(encoding="utf-8")
    problems = []
    actions = []

    # 找到所有问题标题行
    problem_positions = []
    for m in re.finditer(r'^##\s+([🔴🟡🟢])\s+问题\s*\d+\s*[：:]\s*(.+)', content, re.MULTILINE):
        problem_positions.append((m.start(), m.group(1), m.group(2)))

    for i, (pos, level_emoji, title) in enumerate(problem_positions):
        # 确定该问题 section 的结束位置
        if i + 1 < len(problem_positions):
            end_pos = problem_positions[i + 1][0]
        else:
            # 最后一个问题：查找"各问题关联分析"或"数据完整性"等后续章节
            end_match = re.search(r'\n##\s+(?:各问题关联|数据完整性)', content[pos:])
            if end_match:
                end_pos = pos + end_match.start()
            else:
                end_pos = len(content)

        section = content[pos:end_pos]

        # 确定优先级
        priority_map = {"🔴": "🔴严重", "🟡": "🟡注意", "🟢": "🟢观察"}
        priority = priority_map.get(level_emoji, "🟡注意")

        # 数据依据
        data_basis = ""
        data_match = re.search(r'### 数据是什么\n\n(.*?)(?=\n###|\n##|\Z)', section, re.DOTALL)
        if data_match:
            data_basis = data_match.group(1).strip()

        # 业务影响
        impact = ""
        impact_match = re.search(r'### 这意味着什么.*?\n\n(.*?)(?=\n###|\n##|\Z)', section, re.DOTALL)
        if impact_match:
            impact = impact_match.group(1).strip()

        # 根因分析
        root_cause = ""
        root_match = re.search(r'### 为什么会这样.*?\n\n(.*?)(?=\n###|\n##|\Z)', section, re.DOTALL)
        if root_match:
            root_cause = root_match.group(1).strip()

        # 解决建议（完整文本 → 提取每条建议为独立行）
        suggestions = ""
        sug_match = re.search(r'### 具体建议.*?\n\n(.*?)(?=\n###|\n##|\Z)', section, re.DOTALL)
        if sug_match:
            suggestions = sug_match.group(1).strip()

        # 提取建议表中的每条行动项
        action_items = _parse_action_table(suggestions)
        for act in action_items:
            actions.append({
                "日期": date_str,
                "关联问题": _clean_markdown(title, max_len=200),
                "优先级": priority,
                "建议动作": _clean_markdown(act["action"], max_len=200),
                "为什么这样做": _clean_markdown(act["reason"], max_len=400),
                "状态": "待处理",
            })

        # 简短摘要替代完整建议
        sug_summary = _build_suggestion_summary(action_items)

        # 新手解释（从整个报告中找类比理解）
        newbie = ""
        analogy_match = re.search(r'>\s*\*\*类比理解[：:]\*\*\s*(.+?)(?:\n>|\n\n)', section)
        if analogy_match:
            newbie = analogy_match.group(1).strip()

        problems.append({
            "日期": date_str,
            "优先级": priority,
            "问题标题": _clean_markdown(title, max_len=200),
            "数据依据": _clean_markdown(data_basis, max_len=800),
            "业务影响": _clean_markdown(impact, max_len=600),
            "根因分析": _clean_markdown(root_cause, max_len=800),
            "解决建议": sug_summary,
            "新手解释": _clean_markdown(newbie, max_len=400),
            "状态": "待处理",
            "来源报告": f"output/reports/problem_diagnosis_{date_str}.md",
        })

    return problems, actions


def _parse_action_table(md_text: str) -> list:
    """从 markdown 建议表格中解析每条行动建议"""
    items = []
    # 匹配表格行: | 建议文本 | 为什么这样做文本 |
    rows = re.findall(r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|', md_text)
    for row in rows:
        action = row[0].strip()
        reason = row[1].strip()
        # 跳过表头
        if action in ['建议', '------', '---', ''] or '---' in action:
            continue
        if '建议' in action and '为什么' in reason:
            continue
        items.append({"action": action, "reason": reason})
    return items


def _build_suggestion_summary(items: list) -> str:
    """把多条建议压缩为简短摘要"""
    if not items:
        return ""
    lines = []
    for i, item in enumerate(items):
        action = _clean_markdown(item["action"], max_len=80)
        lines.append(f"{i+1}. {action}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════
# 推送到飞书
# ═══════════════════════════════════════════════════

# 需要归一化到 0-1 范围的 Progress 字段（升级后的 ui_type=Progress）
_PROGRESS_FIELDS = {
    "GMV较昨日变化（%）", "订单数较昨日变化（%）", "客单价较昨日变化（%）",
    "退款率-支付口径（%）", "退款率较昨日变化（%）", "7日累计退款率（%）",
    "退款原因TOP1占比（%）", "退款原因TOP2占比（%）",
    "曝光-点击率（%）", "曝光-点击率较昨日变化（%）", "同行曝光-点击率标杆（%）",
    "点击-成交转化率（%）", "点击-成交转化率较昨日变化（%）", "同行点击-成交率基准（%）",
    "曝光较昨日变化（%）",
    "搜索GMV占比（%）", "搜索环比（%）",
    "精选联盟GMV占比（%）", "精选联盟环比（%）",
    "短视频GMV占比（%）", "短视频环比（%）",
    "商城GMV占比（%）",
}


def _to_feishu_fields(data: dict) -> dict:
    """转换字段为飞书 API 格式"""
    fields = {}
    for key, value in data.items():
        if value is None or value == "" or value == 0.0:
            # 保留 0 值的数字，但跳过空文本
            if isinstance(value, (int, float)) and value == 0.0 and key != "日期":
                continue
            if isinstance(value, str) and value == "":
                continue
            if value is None:
                continue

        if key == "日期":
            try:
                parsed = datetime.strptime(str(value), "%Y-%m-%d")
                fields[key] = int(parsed.timestamp() * 1000)
            except ValueError:
                fields[key] = str(value)
        elif isinstance(value, str):
            fields[key] = value
        elif isinstance(value, (int, float)):
            # Progress 字段需要 0-1 范围，将百分比值归一化
            if key in _PROGRESS_FIELDS and abs(value) > 1.0:
                fields[key] = value / 100.0
            else:
                fields[key] = value
        elif isinstance(value, bool):
            fields[key] = value

    return fields


def push_daily_metrics(client, data: dict) -> dict:
    """推送每日指标到表1，支持 upsert"""
    date_str = data["日期"]
    target_ts = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)

    # 查重
    existing = client.get(
        f"/bitable/v1/apps/{APP_TOKEN}/tables/{DAILY_METRICS_TABLE_ID}/records",
        params={"page_size": 10},
    )
    existing_records = existing.get("data", {}).get("items") or []
    matching = [r for r in existing_records
                if r.get("fields", {}).get("日期", 0) == target_ts]

    feishu_fields = _to_feishu_fields(data)

    if matching:
        record_id = matching[0]["record_id"]
        client.put(
            f"/bitable/v1/apps/{APP_TOKEN}/tables/{DAILY_METRICS_TABLE_ID}/records/{record_id}",
            json_body={"fields": feishu_fields},
        )
        print(f"📝 更新每日指标: {record_id}")
        return {"action": "updated", "record_id": record_id}
    else:
        resp = client.post(
            f"/bitable/v1/apps/{APP_TOKEN}/tables/{DAILY_METRICS_TABLE_ID}/records",
            json_body={"fields": feishu_fields},
        )
        record = resp.get("data", {}).get("record", {})
        record_id = record.get("record_id", "")
        print(f"✅ 创建每日指标: {record_id}")
        return {"action": "created", "record_id": record_id}


def push_problems(client, date_str: str, problems: list) -> list:
    """推送问题到表2：先删除当天旧问题，再写入新的"""
    target_ts = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)

    # 1. 查当天已有的问题
    existing = client.get(
        f"/bitable/v1/apps/{APP_TOKEN}/tables/{PROBLEM_TRACKING_TABLE_ID}/records",
        params={"page_size": 100},
    )
    existing_records = existing.get("data", {}).get("items") or []
    old_ids = [r["record_id"] for r in existing_records
               if r.get("fields", {}).get("日期", 0) == target_ts]

    # 2. 删除旧记录
    for rid in old_ids:
        try:
            client.delete(
                f"/bitable/v1/apps/{APP_TOKEN}/tables/{PROBLEM_TRACKING_TABLE_ID}/records/{rid}"
            )
        except FeishuAPIError as e:
            print(f"  ⚠️ 删除旧问题失败: {e}")

    if old_ids:
        print(f"  🗑 清理旧问题: {len(old_ids)} 条")

    # 3. 写入新问题
    results = []
    for p in problems:
        feishu_fields = _to_feishu_fields(p)
        try:
            resp = client.post(
                f"/bitable/v1/apps/{APP_TOKEN}/tables/{PROBLEM_TRACKING_TABLE_ID}/records",
                json_body={"fields": feishu_fields},
            )
            record = resp.get("data", {}).get("record", {})
            results.append(record.get("record_id", ""))
            print(f"  ✅ 问题: {p['问题标题'][:50]}...")
        except FeishuAPIError as e:
            print(f"  ⚠️ 推送失败: {e}")
    return results


def push_actions(client, date_str: str, actions: list) -> list:
    """推送行动建议到表3：先删除当天旧数据，再写入新的"""
    if not actions:
        print("  ℹ️ 无行动建议")
        return []

    target_ts = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)

    # 查当天已有
    existing = client.get(
        f"/bitable/v1/apps/{APP_TOKEN}/tables/{ACTION_TABLE_ID}/records",
        params={"page_size": 200},
    )
    existing_records = existing.get("data", {}).get("items") or []
    old_ids = [r["record_id"] for r in existing_records
               if r.get("fields", {}).get("日期", 0) == target_ts]

    for rid in old_ids:
        try:
            client.delete(
                f"/bitable/v1/apps/{APP_TOKEN}/tables/{ACTION_TABLE_ID}/records/{rid}"
            )
        except FeishuAPIError:
            pass

    if old_ids:
        print(f"  🗑 清理旧建议: {len(old_ids)} 条")

    # 写入
    results = []
    for a in actions:
        feishu_fields = _to_feishu_fields(a)
        try:
            resp = client.post(
                f"/bitable/v1/apps/{APP_TOKEN}/tables/{ACTION_TABLE_ID}/records",
                json_body={"fields": feishu_fields},
            )
            record = resp.get("data", {}).get("record", {})
            results.append(record.get("record_id", ""))
            print(f"  ✅ {a['建议动作'][:60]}...")
        except FeishuAPIError as e:
            print(f"  ⚠️ 推送失败: {e}")
    return results


# ═══════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════

def main():
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"🚀 同步 douyin 数据到飞书: {date_str}\n")

    # 1. 解析日报
    print("📊 解析日报...")
    metrics = parse_daily_metrics(date_str)
    if not metrics:
        print("❌ 无法解析日报")
        sys.exit(1)

    print(f"   GMV: ¥{metrics.get('GMV（元）', 0)}")
    print(f"   订单数: {metrics.get('订单数', 0)}")
    print(f"   退款率: {metrics.get('退款率-支付口径（%）', 0)}%")
    print(f"   转化率: {metrics.get('点击-成交转化率（%）', 0)}%")

    # 2. 解析问题
    print("\n🔍 解析问题诊断...")
    problems, actions = parse_problems(date_str)
    print(f"   发现 {len(problems)} 个问题, {len(actions)} 条行动建议")

    # 3. 连接飞书
    try:
        client = get_client()
    except Exception as e:
        print(f"❌ 飞书客户端初始化失败: {e}")
        sys.exit(1)

    # 4. 推送指标
    print(f"\n--- 表1: 抖音每日指标 ---")
    try:
        result = push_daily_metrics(client, metrics)
    except FeishuAPIError as e:
        print(f"❌ 推送指标失败: {e}")
        sys.exit(1)

    # 5. 推送问题
    print(f"\n--- 表2: 抖音每日问题追踪 ---")
    push_problems(client, date_str, problems)

    # 6. 推送行动建议
    print(f"\n--- 表3: 抖音行动建议明细 ---")
    push_actions(client, date_str, actions)

    # 7. 完成
    base_url = f"https://vcnyjz2su8ck.feishu.cn/base/{APP_TOKEN}"
    print(f"\n✨ 同步完成!")
    print(f"   每日指标: {base_url}/table/{DAILY_METRICS_TABLE_ID}")
    print(f"   问题追踪: {base_url}/table/{PROBLEM_TRACKING_TABLE_ID}")
    print(f"   行动建议: {base_url}/table/{ACTION_TABLE_ID}")


if __name__ == "__main__":
    main()
