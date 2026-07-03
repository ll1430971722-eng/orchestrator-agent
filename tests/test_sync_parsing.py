"""
测试同步脚本中的解析函数

parse_number, parse_change_pct, _clean_markdown 等不依赖飞书 API。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
# 把 feishu mcp 也加入 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp-servers" / "feishu"))

from sync_douyin_to_feishu import (
    parse_number,
    parse_change_pct,
    _clean_markdown,
    _parse_metrics_table,
    _parse_channel_table,
    _parse_after_sales,
    _parse_product_health,
    _parse_refund_details,
)
from sync_to_feishu import _split_sections, parse_daily_summary


class TestParseNumber:
    def test_simple(self):
        assert parse_number("¥62.40") == 62.40

    def test_with_emoji(self):
        assert parse_number("🔴 ¥15.00") == 15.0

    def test_with_percent(self):
        assert parse_number("26.13%") == 26.13

    def test_with_units(self):
        assert parse_number("4单") == 4.0
        assert parse_number("107人") == 107.0

    def test_empty(self):
        assert parse_number("") == 0.0
        assert parse_number("-") == 0.0

    def test_with_comma(self):
        assert parse_number("¥1,632.03") == 1632.03

    def test_with_arrows(self):
        assert parse_number("↑86.69%") == 86.69
        assert parse_number("↓5%") == 5.0


class TestParseChangePct:
    def test_positive(self):
        assert parse_change_pct("+78.03% ↑") == 78.03

    def test_negative(self):
        assert parse_change_pct("-15.5%") == -15.5

    def test_flat(self):
        assert parse_change_pct("持平") == 0.0

    def test_empty(self):
        assert parse_change_pct("") == 0.0
        assert parse_change_pct("-") == 0.0


class TestCleanMarkdown:
    def test_headings(self):
        result = _clean_markdown("### 标题内容")
        assert "标题内容" in result

    def test_bullets(self):
        result = _clean_markdown("- 测试项目")
        assert "测试项目" in result

    def test_table_rows(self):
        md = """| 渠道 | GMV | 变化 |
|------|-----|------|
| 搜索 | ¥100 | ↑10% |"""
        result = _clean_markdown(md)
        assert "搜索" in result
        assert "¥100" in result

    def test_empty(self):
        assert _clean_markdown("") == ""

    def test_max_len_truncation(self):
        long_text = "a" * 1000
        result = _clean_markdown(long_text, max_len=100)
        assert len(result) <= 100

    def test_bold_stripping(self):
        assert "**" not in _clean_markdown("**加粗文字**")
        assert "加粗文字" in _clean_markdown("**加粗文字**")


class TestParseMetricsTable:
    def test_six_column_format(self):
        md = """## 核心指标

| 指标 | 今日值 | 较昨日 | 同行基准 | 评价 |
|------|--------|--------|-------------|------|
| 成交金额 | ¥62.40 | ↑86.69% | ¥412.20 | 🔴 低 |
| 成交订单数 | 4 | ↑86.67% | 21 | 🔴 低 |
| 客单价 | ¥14.35 | ↑12.37% | ¥20.38 | 🟡 中 |
| 退款率(支付时间) | 26.13% | - | - | 🔴 高 |
| 商品曝光人数 | 1601 | ↑75.27% | - | - |"""
        result = _parse_metrics_table(md)
        assert result["gmv"] == 62.40
        assert result["orders"] == 4
        assert result["asp"] == 14.35
        assert result["refund_rate"] == 26.13
        assert result["exposure"] == 1601


class TestParseChannelTable:
    def test_channels(self):
        md = """## 流量结构

| 渠道 | GMV贡献 | 变化 |
|------|---------|------|
| 搜索 | ¥1,632 | ↑22.44% |
| 短视频 | ¥165.6 | ↑203.85% |
| 达人联盟 | ¥453.2 | ↑286.03% |"""
        result = _parse_channel_table(md)
        assert result["search_gmv"] == 1632.0
        assert result["video_gmv"] == 165.6
        assert result["affiliate_gmv"] == 453.2
        assert result["search_change"] == 22.44


class TestParseAfterSales:
    def test_pending_orders(self):
        md = "待发货 3单，待处理售后 5单"
        result = _parse_after_sales(md)
        assert result["pending_ship"] == 3
        assert result["pending_after_sales"] == 5


class TestParseProductHealth:
    def test_excellent(self):
        md = "优秀商品 30个，在售商品 38个"
        result = _parse_product_health(md)
        assert result["excellent"] == 30
        assert result["has_sales"] == 38


class TestParseRefundDetails:
    def test_7day_refund(self):
        md = """7日退款金额：¥880.94
7日退款率：24.63%"""
        result = _parse_refund_details(md)
        assert result["refund_7d_amount"] == 880.94
        assert result["refund_7d_rate"] == 24.63


class TestSplitSections:
    def test_split(self):
        md = """# 标题

## 一句话总结
今天不错。

## 店铺运营
- 销售额 1000
- 订单 50

## 明日关注
- 观察退款率"""
        sections = _split_sections(md)
        assert "今天不错" in sections["一句话总结"]
        assert "销售额 1000" in sections["店铺运营"]
        assert "观察退款率" in sections["明日关注"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
