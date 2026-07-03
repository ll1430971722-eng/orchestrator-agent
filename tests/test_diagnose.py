"""
测试 diagnose_problems.py 诊断逻辑

使用模拟数据验证各种场景的自动诊断是否正确触发。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from diagnose_problems import diagnose, _safe_float


class TestSafeFloat:
    def test_normal(self):
        assert _safe_float(3.14) == 3.14

    def test_none(self):
        assert _safe_float(None) == 0.0

    def test_string(self):
        assert _safe_float("abc") == 0.0

    def test_int(self):
        assert _safe_float(42) == 42.0


class TestDiagnoseGmvDecline:
    """GMV 下降诊断"""

    def test_high_risk_gmv_decline(self):
        """GMV 下降 35% 应触发高风险"""
        data = {
            "gmv": 650, "gmv_change_pct": -35.0,
            "refund_rate": 5.0, "refund_rate_change_pct": 0,
            "ad_roi": 3.0, "ad_spend": 0,
        }
        problems = diagnose(data)
        gmv_problems = [p for p in problems if "GMV" in p["title"]]
        assert len(gmv_problems) >= 1
        assert gmv_problems[0]["priority"] == "高"

    def test_medium_risk_gmv_decline(self):
        """GMV 下降 20% 应触发中风险"""
        data = {
            "gmv": 800, "gmv_change_pct": -20.0,
            "refund_rate": 5.0, "refund_rate_change_pct": 0,
            "ad_roi": 3.0, "ad_spend": 0,
        }
        problems = diagnose(data)
        gmv_problems = [p for p in problems if "GMV" in p["title"]]
        assert len(gmv_problems) >= 1
        assert gmv_problems[0]["priority"] == "中"

    def test_no_gmv_problem(self):
        """GMV 上涨不触发诊断"""
        data = {
            "gmv": 1000, "gmv_change_pct": 10.0,
            "refund_rate": 5.0, "refund_rate_change_pct": 0,
            "ad_roi": 3.0, "ad_spend": 0,
        }
        problems = diagnose(data)
        gmv_problems = [p for p in problems if "GMV" in p["title"]]
        assert len(gmv_problems) == 0


class TestDiagnoseRefundRate:
    """退款率诊断"""

    def test_refund_rate_critical(self):
        """退款率 >20% 触发高风险"""
        data = {
            "gmv": 500, "gmv_change_pct": 5.0,
            "refund_rate": 25.0, "refund_rate_change_pct": 0,
            "refund_amount": 200,
            "ad_roi": 3.0, "ad_spend": 0,
        }
        problems = diagnose(data)
        refund_problems = [p for p in problems if "退款率" in p["title"]]
        assert len(refund_problems) >= 1
        assert refund_problems[0]["priority"] == "高"

    def test_refund_rate_elevated(self):
        """退款率 10-20% 触发中风险"""
        data = {
            "gmv": 500, "gmv_change_pct": 5.0,
            "refund_rate": 15.0, "refund_rate_change_pct": 0,
            "refund_amount": 100,
            "ad_roi": 3.0, "ad_spend": 0,
        }
        problems = diagnose(data)
        refund_problems = [p for p in problems if "退款率" in p["title"]]
        assert len(refund_problems) >= 1

    def test_refund_rate_normal(self):
        """退款率 <10% 不触发"""
        data = {
            "gmv": 500, "gmv_change_pct": 5.0,
            "refund_rate": 5.0, "refund_rate_change_pct": 0,
            "refund_amount": 10,
            "ad_roi": 3.0, "ad_spend": 0,
        }
        problems = diagnose(data)
        refund_problems = [p for p in problems if "退款率" in p["title"]]
        assert len(refund_problems) == 0


class TestDiagnoseAdRoi:
    """广告 ROI 诊断"""

    def test_roi_loss(self):
        """ROI < 1 触发高风险"""
        data = {
            "gmv": 1000, "gmv_change_pct": 5.0,
            "refund_rate": 5.0, "refund_rate_change_pct": 0,
            "ad_roi": 0.5, "ad_spend": 500,
        }
        problems = diagnose(data)
        roi_problems = [p for p in problems if "ROI" in p["title"]]
        assert len(roi_problems) >= 1
        assert roi_problems[0]["priority"] == "高"

    def test_roi_healthy(self):
        """ROI >= 1 不触发"""
        data = {
            "gmv": 1000, "gmv_change_pct": 5.0,
            "refund_rate": 5.0, "refund_rate_change_pct": 0,
            "ad_roi": 2.5, "ad_spend": 200,
        }
        problems = diagnose(data)
        roi_problems = [p for p in problems if "ROI" in p["title"]]
        assert len(roi_problems) == 0

    def test_roi_no_spend(self):
        """没花广告费不触发"""
        data = {
            "gmv": 1000, "gmv_change_pct": 5.0,
            "refund_rate": 5.0, "refund_rate_change_pct": 0,
            "ad_roi": 0, "ad_spend": 0,
        }
        problems = diagnose(data)
        roi_problems = [p for p in problems if "ROI" in p["title"]]
        assert len(roi_problems) == 0


class TestDiagnoseConversion:
    """转化率诊断"""

    def test_conversion_decline(self):
        """转化率下降 >20% 触发"""
        data = {
            "gmv": 1000, "gmv_change_pct": 5.0,
            "refund_rate": 5.0, "refund_rate_change_pct": 0,
            "click_conversion_rate": 2.0,
            "click_conversion_rate_change_pct": -25.0,
            "ad_roi": 3.0, "ad_spend": 0,
        }
        problems = diagnose(data)
        conv_problems = [p for p in problems if "转化率" in p["title"]]
        assert len(conv_problems) >= 1


class TestDiagnoseEmptyData:
    """空数据/无异常场景"""

    def test_all_normal(self):
        """所有指标正常时返回空列表"""
        data = {
            "gmv": 1000, "gmv_change_pct": 5.0,
            "refund_rate": 3.0, "refund_rate_change_pct": 0,
            "click_conversion_rate": 10.0,
            "click_conversion_rate_change_pct": 5.0,
            "ad_roi": 3.0, "ad_spend": 100,
        }
        problems = diagnose(data)
        assert len(problems) == 0

    def test_problems_sorted_by_priority(self):
        """多个问题时按优先级排序"""
        data = {
            "gmv": 500, "gmv_change_pct": -35.0,  # 高
            "refund_rate": 25.0, "refund_rate_change_pct": 0, "refund_amount": 200,  # 高
            "ad_roi": 0.3, "ad_spend": 1000,  # 高
        }
        problems = diagnose(data)
        # 所有高风险应该排在前面
        for p in problems[:2]:
            assert p["priority"] == "高"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
