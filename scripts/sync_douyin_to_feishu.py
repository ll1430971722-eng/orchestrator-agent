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
TRACKING_TABLE_ID = "tbl13n3VVldrXWmD"  # 问题 & 行动追踪（合并表）

DOUYIN_REPORTS = ORCHESTRATOR_ROOT / "output" / "reports"


# ═══════════════════════════════════════════════════
# 解析 douyin 日报（6/15新格式：YYYY-MM-DD-daily-report.md）
# ═══════════════════════════════════════════════════

def parse_number(text: str) -> float:
    """从文本中提取数字，去掉 ¥ % 单 人 ** 等"""
    text = str(text).strip()
    text = text.replace('**', '')
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
    """解析 douyin 日报为结构化指标，兼容新旧两种格式"""
    # 先尝试新格式 YYYY-MM-DD-daily-report.md
    filepath = DOUYIN_REPORTS / f"{date_str}-daily-report.md"
    if not filepath.exists():
        # 回退到旧格式 daily_report_YYYY-MM-DD.md
        filepath = DOUYIN_REPORTS / f"daily_report_{date_str}.md"
    if not filepath.exists():
        print(f"❌ 日报不存在: {filepath}")
        return None

    content = filepath.read_text(encoding="utf-8")

    # ── 核心指标表格 ──
    metrics = _parse_metrics_table(content)

    # ── 店铺评分 ──
    score_match = re.search(r'体验分[：:]\s*(\d+)\s*分', content)
    store_score = int(score_match.group(1)) if score_match else 0

    product_score_match = re.search(r'商品[：:]?\s*(\d+)\s*分', content)
    product_score = int(product_score_match.group(1)) if product_score_match else 0

    logistics_score_match = re.search(r'物流[：:]?\s*(\d+)\s*分', content)
    logistics_score = int(logistics_score_match.group(1)) if logistics_score_match else 0

    service_score_match = re.search(r'服务[：:]?\s*(\d+)\s*分', content)
    service_score = int(service_score_match.group(1)) if service_score_match else 0

    # ── 漏斗 ──
    funnel = ""
    funnel_match = re.search(r'## 流量结构\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if funnel_match:
        funnel = funnel_match.group(1).strip()

    # ── 一句话总结 ──
    one_liner = ""
    oneliner_match = re.search(r'## 一句话总结\n\n(.+?)(?=\n##|\n---|\Z)', content, re.DOTALL)
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
    tm_match = re.search(r'## 明日关注\n\n(.*?)(?=\n##|\n---|\Z)', content, re.DOTALL)
    if tm_match:
        tomorrow = tm_match.group(1).strip()

    # ── 渠道亮点文本 ──
    channel_highlight = ""
    ch_match = re.search(r'## 各渠道表现.*?\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if ch_match:
        channel_highlight = ch_match.group(1).strip()

    # 客单价同行基准
    asp_peer = 20.38
    asp_peer_m = re.search(r'同行基准.*?¥([\d.]+)', content)
    if not asp_peer_m:
        asp_peer_m = re.search(r'同行.*?客单价.*?¥([\d.]+)', content)
    if asp_peer_m:
        asp_peer = float(asp_peer_m.group(1))

    return {
        "日期": date_str,
        "GMV（元）": metrics.get("gmv", 0),
        "GMV较昨日变化（%）": metrics.get("gmv_change", 0),
        "订单数": metrics.get("orders", 0),
        "订单数较昨日变化（%）": metrics.get("orders_change", 0),
        "客单价（元）": metrics.get("asp", 0),
        "客单价较昨日变化（%）": metrics.get("asp_change", 0),
        "同行客单价基准（元）": asp_peer,
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
    """解析核心指标表格（兼容新旧格式）"""
    result = {}

    # 找表格区域 - 兼容多种格式
    table_match = re.search(r'## (?:核心指标|一、核心指标)\n\n(.*?)(?=\n\n##|\n\n---)', content, re.DOTALL)
    if not table_match:
        table_match = re.search(r'\|\s*指标\s*\|(.*?)(?=\n\n\*\*|## 与)', content, re.DOTALL)
    if not table_match:
        return result

    table_text = table_match.group(0)

    # 逐行匹配: | 指标名 | 今日值 | 较昨日 | 同行基准 | 评价 |
    rows = re.findall(r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', table_text)
    if not rows:
        # 尝试3列格式
        rows = re.findall(r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', table_text)
        for row in rows:
            indicator = row[0].strip()
            today_val = row[1].strip()
            change_val = row[2].strip() if len(row) > 2 else ""
            peer_val = ""
            _map_metric(result, indicator, today_val, change_val, peer_val)
        return result

    for row in rows:
        indicator = row[0].strip()
        today_val = row[1].strip()
        change_val = row[2].strip()
        peer_val = row[3].strip() if len(row) > 3 else ""
        _map_metric(result, indicator, today_val, change_val, peer_val)

    return result


def _map_metric(result, indicator, today_val, change_val, peer_val):
    """映射指标值"""
    # GMV
    if '成交金额' in indicator or 'GMV' in indicator or '支付金额' in indicator:
        if not result.get("gmv"):
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
    elif '退款率' in indicator:
        result["refund_rate"] = parse_number(today_val)
        result["refund_rate_change"] = parse_change_pct(change_val)
    # 退款金额
    elif '退款金额' in indicator:
        result["refund_amount"] = parse_number(today_val)
    # 曝光人数
    elif '曝光人数' in indicator or '商品曝光' in indicator:
        result["exposure"] = int(parse_number(today_val))
        result["exposure_change"] = parse_change_pct(change_val)
    # 曝光-点击率
    elif '曝光-点击' in indicator or '曝光→点击' in indicator:
        result["exposure_click_rate"] = parse_number(today_val)
        result["exposure_click_rate_change"] = parse_change_pct(change_val)
        if peer_val and peer_val != '-':
            result["exposure_click_rate_peer"] = parse_number(peer_val)
    # 点击-成交转化率
    elif '点击-成交' in indicator or '点击→成交' in indicator:
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
    elif '广告消耗' in indicator or '投放消耗' in indicator:
        result["ad_spend"] = parse_number(today_val)
    # 支出金额
    elif '支出金额' in indicator:
        result["ad_spend"] = parse_number(today_val)


def _parse_channel_table(content: str) -> dict:
    """解析渠道表现"""
    result = {}
    table_match = re.search(r'## (?:流量结构|四、各渠道表现)\n\n(.*?)(?=\n##|\n---)', content, re.DOTALL)
    if not table_match:
        return result

    table_text = table_match.group(0)
    rows = re.findall(r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', table_text)
    if not rows:
        rows = re.findall(r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', table_text)

    for row in rows:
        channel = row[0].strip()
        gmv_str = row[1].strip() if len(row) > 1 else ""
        pct_str = row[2].strip() if len(row) > 2 else ""
        change_str = row[3].strip() if len(row) > 3 else ""

        if '搜索' in channel:
            result["search_gmv"] = parse_number(gmv_str)
            result["search_pct"] = parse_number(pct_str)
            result["search_change"] = parse_change_pct(change_str)
        elif '联盟' in channel or '达人' in channel:
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
    m = re.search(r'待发货.*?(\d+)\s*单', content)
    if m: result["pending_ship"] = int(m.group(1))
    m = re.search(r'待处理售后.*?(\d+)\s*单', content)
    if m: result["pending_after_sales"] = int(m.group(1))
    return result


def _parse_product_health(content: str) -> dict:
    """解析商品健康度"""
    result = {}
    m = re.search(r'优秀商品.*?(\d+)\s*个', content)
    if m: result["excellent"] = int(m.group(1))
    m = re.search(r'优秀[：:]\s*(\d+)', content)
    if m: result["excellent"] = int(m.group(1))
    m = re.search(r'在售商品[：:]\s*(\d+)', content)
    if m: result["has_sales"] = int(m.group(1))
    return result


def _parse_refund_details(content: str) -> dict:
    """解析退款详细数据"""
    result = {}

    # 7日累计退款
    m = re.search(r'7日退款金额[：:]\s*¥([\d,.]+)', content)
    if m: result["refund_7d_amount"] = parse_number(m.group(1))
    m = re.search(r'7日退款率[：:]\s*([\d.]+)%', content)
    if m: result["refund_7d_rate"] = float(m.group(1))

    # 今日退款金额
    m = re.search(r'退款金额[（(]退款时间[）)].*?¥([\d,.]+)', content)
    if m: result["refund_amount_today"] = parse_number(m.group(1))

    # 今日退款订单数
    m = re.search(r'退款订单数[（(]退款时间[）)].*?(\d+)', content)
    if m: result["refund_orders_today"] = int(m.group(1))

    # 退款原因
    reason_match = re.search(r'TOP退款原因.*?\n(.*?)(?=\n\n|\n##|\Z)', content, re.DOTALL)
    if reason_match:
        reasons_text = reason_match.group(1)
        items = re.findall(r'(.+?)[（(]([\d.]+)%[）)]', reasons_text)
        if len(items) >= 1:
            result["refund_reason_top1"] = items[0][0].strip().lstrip('| ')
            result["refund_reason_top1_pct"] = float(items[0][1])
        if len(items) >= 2:
            result["refund_reason_top2"] = items[1][0].strip().lstrip('| ')
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

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped in ['---', '---', '***']:
            if clean_lines and clean_lines[-1] != '':
                clean_lines.append('')
            continue
        if re.match(r'^\|[\s\-:|]+\|$', stripped):
            continue
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            cells = [c for c in cells if c and not re.match(r'^[🟢🟡🔴⚠️✅]+$', c)]
            if cells:
                clean_lines.append(' · '.join(cells))
            continue
        if stripped.startswith('### '):
            clean_lines.append(f"【{stripped[4:].strip()}】")
            continue
        if stripped.startswith('## '):
            clean_lines.append(f"▎{stripped[3:].strip()}")
            continue
        if stripped.startswith('> '):
            clean_lines.append(stripped[2:].strip())
            continue
        if re.match(r'^[\-\*]\s+', stripped):
            clean_lines.append(f"• {stripped[2:].strip()}")
            continue
        clean_lines.append(stripped)

    result = '\n'.join(clean_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = result.replace('**', '').replace('__', '').replace('`', '')

    if len(result) > max_len:
        result = result[:max_len]
        last_break = max(result.rfind('。'), result.rfind('\n'), result.rfind('.'))
        if last_break > max_len // 2:
            result = result[:last_break + 1]
        result = result.strip()

    return result


# ═══════════════════════════════════════════════════
# 解析问题诊断（6/15新格式）
# ═══════════════════════════════════════════════════

def parse_tracking_records(date_str: str) -> list:
    """解析诊断报告，返回合并的问题+行动记录列表"""
    filepath = DOUYIN_REPORTS / f"{date_str}-diagnosis.md"
    if not filepath.exists():
        filepath = DOUYIN_REPORTS / f"problem_diagnosis_{date_str}.md"
    if not filepath.exists():
        print(f"⚠️ 诊断报告不存在: {filepath}")
        return []

    content = filepath.read_text(encoding="utf-8")
    records = []

    # 找到所有问题标题
    problem_positions = []
    for m in re.finditer(r'### 问题\s*\d+[：:]\s*(.+)', content):
        title = m.group(1).strip()
        priority = "🟡 注意"
        if '🔴' in title:
            priority = "🔴 严重"
        elif '🟡' in title:
            priority = "🟡 注意"
        elif '🟢' in title:
            priority = "🟢 观察"
        problem_positions.append((m.start(), priority, title))

    for i, (pos, priority, title) in enumerate(problem_positions):
        if i + 1 < len(problem_positions):
            end_pos = problem_positions[i + 1][0]
        else:
            end_pos = len(content)
        section = content[pos:end_pos]

        # 数据依据
        data_basis = ""
        data_match = re.search(r'\*\*数据依据[：:]\*\*\n\n(.*?)(?=\n\*\*|\n###|\Z)', section, re.DOTALL)
        if data_match:
            data_basis = data_match.group(1).strip()

        # 根因分析: 从"可能原因"到下一个 bold 标题（建议验证/具体解决/新手解释）
        root_cause = ""
        root_match = re.search(
            r'\*\*可能原因.*?\*\*\s*\n(.*?)(?=\n\*\*建议验证|\n\*\*具体解决|\n\*\*💡|\n\*\*未来|\n###|\Z)',
            section, re.DOTALL
        )
        if root_match:
            root_cause = root_match.group(1).strip()

        # 新手解释
        newbie = ""
        newbie_match = re.search(r'\*\*💡 新手解释[：:]\*\*\s*(.+?)(?:\n\n|\n\*\*)', section, re.DOTALL)
        if newbie_match:
            newbie = newbie_match.group(1).strip()

        # 合并分析文本
        analysis_parts = []
        if data_basis:
            analysis_parts.append(f"数据: {data_basis}")
        if root_cause:
            analysis_parts.append(f"根因: {root_cause}")
        if newbie:
            analysis_parts.append(f"说明: {newbie}")
        analysis = "\n\n".join(analysis_parts)

        # 提取"具体解决方案"章节的行动表格（只在这个章节内解析，避免误解析"风险评估"表）
        suggestions = ""
        sug_match = re.search(
            r'\*\*具体解决方案[：:]\*\*\n\n(.*?)(?=\n\*\*|\n###|\n---|\Z)',
            section, re.DOTALL
        )
        if sug_match:
            suggestions = sug_match.group(1).strip()

        action_items = _parse_action_table_new(suggestions)

        # 清理问题分析 — 移除原始 markdown 表格行
        clean_analysis = _clean_analysis_text(analysis)

        if action_items:
            # 每个行动一条记录
            for act in action_items:
                records.append({
                    "日期": date_str,
                    "问题标题": _clean_markdown(title, max_len=200),
                    "优先级": priority,
                    "问题分析": _clean_markdown(clean_analysis, max_len=1000),
                    "解决动作": _clean_markdown(act["action"], max_len=200),
                    "预期效果": act.get("effect", ""),
                    "难度": act.get("difficulty", ""),
                    "负责人": act.get("owner", ""),
                    "状态": "待处理",
                })
        else:
            # 没有解析出行动，只存问题
            records.append({
                "日期": date_str,
                "问题标题": _clean_markdown(title, max_len=200),
                "优先级": priority,
                "问题分析": _clean_markdown(analysis, max_len=1000),
                "状态": "待处理",
            })

    return records


def _clean_analysis_text(analysis: str) -> str:
    """清理分析文本：移除残留的 markdown 表格行和多余格式"""
    if not analysis:
        return ""
    lines = analysis.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append(line)
            continue
        # 跳过 markdown 表格行（以 | 开头和结尾，或只是分隔线）
        if stripped.startswith('|'):
            continue
        cleaned.append(line)
    return '\n'.join(cleaned)


def _parse_action_table_new(md_text: str) -> list:
    """从markdown表格解析行动建议，提取全部4列：方案/预期效果/难度/负责人"""
    items = []
    rows = re.findall(r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|', md_text)
    for row in rows:
        action = row[0].strip()
        effect = row[1].strip() if len(row) > 1 else ""
        difficulty = row[2].strip() if len(row) > 2 else ""
        owner = row[3].strip() if len(row) > 3 else ""
        # 跳过表头行
        if action in ['方案', '------', '---', '', '风险'] or '---' in action:
            continue
        if action in ['方案', '预期效果', '风险', '严重度']:
            continue
        items.append({
            "action": action,
            "effect": effect,
            "difficulty": difficulty,
            "owner": owner,
        })
    return items


# ═══════════════════════════════════════════════════
# 推送到飞书
# ═══════════════════════════════════════════════════

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
            fields[key] = value
        elif isinstance(value, bool):
            fields[key] = value

    return fields


def push_daily_metrics(client, data: dict) -> dict:
    """推送每日指标到表1，支持 upsert"""
    date_str = data["日期"]
    target_ts = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)

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


def push_tracking_records(client, date_str: str, records: list) -> list:
    """推送问题+行动到合并追踪表：先删当天旧数据，再写入新的"""
    if not records:
        print("  ℹ️ 无追踪记录")
        return []

    target_ts = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)

    existing = client.get(
        f"/bitable/v1/apps/{APP_TOKEN}/tables/{TRACKING_TABLE_ID}/records",
        params={"page_size": 100},
    )
    existing_records = existing.get("data", {}).get("items") or []
    old_ids = [r["record_id"] for r in existing_records
               if r.get("fields", {}).get("日期", 0) == target_ts]

    for rid in old_ids:
        try:
            client.delete(
                f"/bitable/v1/apps/{APP_TOKEN}/tables/{TRACKING_TABLE_ID}/records/{rid}"
            )
        except FeishuAPIError as e:
            print(f"  ⚠️ 删除旧记录失败: {e}")

    if old_ids:
        print(f"  🗑 清理旧记录: {len(old_ids)} 条")

    results = []
    for r in records:
        feishu_fields = _to_feishu_fields(r)
        try:
            resp = client.post(
                f"/bitable/v1/apps/{APP_TOKEN}/tables/{TRACKING_TABLE_ID}/records",
                json_body={"fields": feishu_fields},
            )
            record = resp.get("data", {}).get("record", {})
            results.append(record.get("record_id", ""))
            action = r.get('解决动作', r.get('问题标题', ''))[:50]
            print(f"  ✅ {action}...")
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

    # 2. 解析诊断报告
    print("\n🔍 解析问题诊断...")
    records = parse_tracking_records(date_str)
    print(f"   发现 {len(records)} 条追踪记录")

    # 3. 连接飞书
    try:
        client = get_client()
    except Exception as e:
        print(f"❌ 飞书客户端初始化失败: {e}")
        sys.exit(1)

    # 4. 推送指标
    print(f"\n--- 每日指标 ---")
    try:
        result = push_daily_metrics(client, metrics)
    except FeishuAPIError as e:
        print(f"❌ 推送指标失败: {e}")
        sys.exit(1)

    # 5. 推送问题 & 行动（合并表）
    print(f"\n--- 问题 & 行动追踪 ---")
    push_tracking_records(client, date_str, records)

    # 6. 完成
    base_url = f"https://vcnyjz2su8ck.feishu.cn/base/{APP_TOKEN}"
    print(f"\n✨ 同步完成!")
    print(f"   每日指标: {base_url}/table/{DAILY_METRICS_TABLE_ID}")
    print(f"   问题追踪: {base_url}/table/{TRACKING_TABLE_ID}")


if __name__ == "__main__":
    main()
