"""
统一配置管理

所有硬编码的 APP_TOKEN、表 ID、Base URL 等集中在这里。
优先从环境变量读取，其次使用默认值。

用法:
    from scripts.config import FEISHU_APP_TOKEN, TABLE_DAILY_METRICS
    # 或在 scripts/ 目录下:
    from config import FEISHU_APP_TOKEN, TABLE_DAILY_METRICS
"""

import os
from pathlib import Path

# ── 项目根目录 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ═══════════════════════════════════════════════════
# 飞书 Base 配置
# ═══════════════════════════════════════════════════

FEISHU_APP_TOKEN = os.getenv("FEISHU_BASE_TOKEN", "GPFtbIOhCafB4HsANmVcbFOan4f")
FEISHU_BASE_URL = os.getenv("FEISHU_BASE_URL", "https://vcnyjz2su8ck.feishu.cn")

# ── 表 ID ──
TABLE_DAILY_METRICS = os.getenv("TABLE_DAILY_METRICS", "tblK15Duu70dPX6G")       # 抖音每日指标表
TABLE_ISSUES_ACTIONS = os.getenv("TABLE_ISSUES_ACTIONS", "tbl13n3VVldrXWmD")      # 问题 & 行动追踪表
TABLE_DAILY_OVERVIEW = os.getenv("TABLE_DAILY_OVERVIEW", "tbldtOCO6pR5g7bP")      # 每日运营概览表
TABLE_DAILY_TRACKING = os.getenv("TABLE_DAILY_TRACKING", "tblLck1taVRaxldS")       # 每日运营追踪表

# ── 完整 URL ──
def table_url(table_id: str) -> str:
    return f"{FEISHU_BASE_URL}/base/{FEISHU_APP_TOKEN}/table/{table_id}"


# ═══════════════════════════════════════════════════
# 路径配置
# ═══════════════════════════════════════════════════

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_REPORTS = PROJECT_ROOT / "output" / "reports"
OUTPUT_DAILY_SUMMARIES = PROJECT_ROOT / "output" / "daily_summaries"
OUTPUT_PENDING_REVIEW = PROJECT_ROOT / "output" / "pending_review"
INPUT_TASKS = PROJECT_ROOT / "input" / "tasks"
MEMORY_DIR = PROJECT_ROOT / "memory"

# ── 飞书 MCP 路径 ──
FEISHU_MCP_DIR = PROJECT_ROOT / "mcp-servers" / "feishu"


# ═══════════════════════════════════════════════════
# 业务配置
# ═══════════════════════════════════════════════════

# 抖店同行基准（兜底值，日报中实际值优先）
DEFAULT_ASP_PEER = 20.38  # 同行客单价基准（元）

# ── 诊断阈值（来自 docs/metrics_rules.md） ──
THRESHOLD_GMV_DECLINE_HIGH = 0.30       # GMV 日环比下降 > 30% → 高风险
THRESHOLD_GMV_DECLINE_MEDIUM = 0.15     # GMV 日环比下降 15-30% → 中等风险
THRESHOLD_REFUND_RATE_MULTIPLIER = 1.5  # 退款率 > 行业均值 × 1.5 → 高风险
THRESHOLD_REFUND_CONSECUTIVE_DAYS = 3   # 退款率连续 N 天上涨 → 需要排查
THRESHOLD_CONVERSION_DECLINE = 0.20     # 支付转化率日环比下降 > 20% → 需要排查
THRESHOLD_ROI_LOSS = 1.0                # ROI < 1 → 亏损
THRESHOLD_ROI_DECLINE_DAYS = 3          # ROI 连续 N 天下降 → 需要排查
THRESHOLD_EXPOSURE_DECLINE = 0.30       # 曝光日环比下降 > 30% → 需要排查
THRESHOLD_CLICK_RATE_DECLINE = 0.20     # 点击率日环比下降 > 20% → 主图或标题问题


# ═══════════════════════════════════════════════════
# 飞书 MCP 配置
# ═══════════════════════════════════════════════════

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_TENANT_DOMAIN = os.getenv("FEISHU_TENANT_DOMAIN", "")  # 默认空，不硬编码 bytedance


# ═══════════════════════════════════════════════════
# 数据文件约定
# ═══════════════════════════════════════════════════

RAW_DATA_FILES = ["orders.json", "products.json", "after_sales.json", "ads.json"]

REPORT_FILENAME_FORMATS = {
    "daily": "{date}-daily-report.md",
    "daily_legacy": "daily_report_{date}.md",
    "diagnosis": "{date}-diagnosis.md",
    "diagnosis_legacy": "problem_diagnosis_{date}.md",
    "action_plan": "{date}-action-plan.md",
    "future_rec": "{date}-future-recommendations.md",
    "summary": "{date}-summary.md",
}


def get_report_path(report_type: str, date_str: str) -> Path:
    """根据类型和日期返回报告路径"""
    fmt = REPORT_FILENAME_FORMATS.get(report_type, "{date}-{type}.md")
    filename = fmt.format(date=date_str, type=report_type)
    return OUTPUT_REPORTS / filename
