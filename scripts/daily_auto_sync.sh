#!/bin/bash
# ============================================================
# 每日自动同步脚本 — 抖店采集 → 仪表盘 → 飞书
# 由 cron/launchd 定时调用
# ============================================================
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$BASE_DIR/data/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily-sync-$(date +%Y-%m-%d).log"

echo "========================================" >> "$LOG_FILE"
echo "🕐 $(date '+%Y-%m-%d %H:%M') — 开始每日同步" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Step 1: 抖店数据采集（带订单明细，确保昨日对比数据准确）
echo "▶ Step 1: 抖店数据采集（带订单明细）..." >> "$LOG_FILE"
cd "$BASE_DIR" && python3 scripts/scrape_douyin_pw.py --orders --max-days 2 >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 抖店采集失败" >> "$LOG_FILE"
    exit 1
fi

# Step 2: 转换为仪表盘格式
echo "▶ Step 2: 转换到仪表盘格式..." >> "$LOG_FILE"
python3 scripts/scraped_to_dashboard.py --platform douyin >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 数据转换失败" >> "$LOG_FILE"
    exit 1
fi

# Step 3: 同步到飞书
echo "▶ Step 3: 同步到飞书..." >> "$LOG_FILE"
python3 scripts/sync_to_feishu.py --platform douyin >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 飞书同步失败" >> "$LOG_FILE"
    exit 1
fi

echo "✅ $(date '+%Y-%m-%d %H:%M') — 每日同步完成" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
