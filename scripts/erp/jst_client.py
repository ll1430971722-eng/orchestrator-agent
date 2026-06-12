"""
聚水潭 ERP Open API 统一客户端

基于官方示例 (api_call.py) 实现:
  - Content-Type: application/x-www-form-urlencoded
  - 签名: MD5(AppSecret + sorted_key1 + val1 + key2 + val2 + ...)
  - 业务参数: biz 字段 (JSON 字符串)

用法:
  from scripts.erp.jst_client import get_client
  client = get_client()
  resp = client.call("/open/shops/query", {"page_index": 1, "page_size": 20})
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)


class JSTAPIError(Exception):
    """聚水潭 API 错误"""

    def __init__(self, code: int, msg: str, raw: dict = None):
        self.code = code
        self.msg = msg
        self.raw = raw or {}
        super().__init__(f"聚水潭 API 错误 [{code}]: {msg}")


class JSTClient:
    """聚水潭开放平台 API 客户端

    基于官方 Python 示例实现签名和请求格式。
    生产 HOST: https://openapi.jushuitan.com
    """

    PRODUCTION_HOST = "https://openapi.jushuitan.com"

    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    MIN_INTERVAL = 0.2

    def __init__(self):
        self.app_key = os.getenv("JST_APP_KEY")
        self.app_secret = os.getenv("JST_APP_SECRET")
        self.access_token = os.getenv("JST_ACCESS_TOKEN", "")
        self.host = os.getenv("JST_HOST", self.PRODUCTION_HOST)

        if not self.app_key or not self.app_secret:
            raise ValueError(
                "JST_APP_KEY 和 JST_APP_SECRET 未设置。"
                "请在 orchestrator-agent/.env 文件中配置。"
            )

        self._last_request_at: float = 0

    # ---- 签名算法 ----

    def _sign(self, params: Dict[str, Any]) -> str:
        """官方签名: MD5(AppSecret + sorted_key1 + val1 + sorted_key2 + val2 + ...)
        'sign' 字段不参与签名
        """
        sorted_keys = sorted(k for k in params.keys() if k != "sign")
        raw = self.app_secret
        for k in sorted_keys:
            raw += str(k)
            raw += str(params[k])
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _build_body(self, biz_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """构建请求 body（含签名），返回 form 参数 dict"""
        params = {
            "access_token": self.access_token,
            "app_key": self.app_key,
            "timestamp": int(time.time()),
            "version": 2,
            "charset": "utf-8",
        }
        if biz_params:
            params["biz"] = json.dumps(biz_params, ensure_ascii=False)
        else:
            params["biz"] = "{}"

        params["sign"] = self._sign(params)
        return params

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_at
        if elapsed < self.MIN_INTERVAL:
            time.sleep(self.MIN_INTERVAL - elapsed)

    # ---- 核心请求方法 ----

    def call(
        self,
        api_method: str,
        biz_params: Optional[Dict[str, Any]] = None,
        *,
        retries: int = None,
    ) -> Dict[str, Any]:
        """调用聚水潭 API

        Args:
            api_method: API 路径，如 "/open/shops/query"
            biz_params: 业务参数 dict，放入 biz 字段
            retries: 重试次数

        Returns:
            API 响应解析后的 dict
        """
        retries = retries if retries is not None else self.MAX_RETRIES

        body = self._build_body(biz_params)
        url = f"{self.host}{api_method}"
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}

        last_error = None

        for attempt in range(retries + 1):
            try:
                self._rate_limit()
                resp = requests.post(url, data=body, headers=headers, timeout=30)
                self._last_request_at = time.time()

                try:
                    data = resp.json()
                except ValueError:
                    resp.raise_for_status()
                    raise JSTAPIError(-1, f"响应非 JSON: {resp.text[:500]}")

                code = data.get("code", -1)
                if code == 0:
                    return data.get("data", data)

                if code in (401, 402, 403):
                    raise JSTAPIError(code, data.get("msg", data.get("message", "鉴权失败")), data)

                raise JSTAPIError(code, data.get("msg", data.get("message", "未知错误")), data)

            except requests.RequestException as e:
                last_error = e
                if attempt < retries:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue

        raise JSTAPIError(-1, f"网络请求失败（重试{retries}次后）: {last_error}")

    def paginated_call(
        self,
        api_method: str,
        biz_params: Optional[Dict[str, Any]] = None,
        *,
        page_key: str = "page_index",
        size_key: str = "page_size",
        page_size: int = 50,
        max_pages: int = 500,
        list_key: str = "datas",
    ) -> list:
        """分页拉取全部数据"""
        all_items = []
        base = dict(biz_params) if biz_params else {}

        for page in range(1, max_pages + 1):
            params = {**base, page_key: page, size_key: page_size}
            data = self.call(api_method, params)

            items = data.get(list_key) if isinstance(data, dict) else None

            if items is None and isinstance(data, dict):
                for candidate in ("datas", "items", "list", "records"):
                    if data.get(candidate):
                        items = data[candidate]
                        break
                if items is None:
                    for v in data.values():
                        if isinstance(v, list):
                            items = v
                            break

            if isinstance(data, list):
                items = data

            if not items:
                break

            all_items.extend(items)

            if isinstance(data, dict) and data.get("has_next") is False:
                break
            if len(items) < page_size:
                break

        return all_items

    # ================================================================
    # 常用 API 封装（路径均来自聚水潭官方文档）
    # ================================================================

    # -- 基础API（默认有权限） --
    def query_shops(self, **kwargs) -> list:
        """店铺列表"""
        return self.paginated_call("/open/shops/query", kwargs)

    # -- 商品API --
    def query_sku(self, sku_ids: list = None, **kwargs) -> list:
        """普通商品资料查询（按sku）"""
        params = dict(kwargs)
        if sku_ids:
            params["sku_ids"] = ",".join(str(x) for x in sku_ids)
        return self.paginated_call("/open/sku/query", params)

    def query_mall_items(self, **kwargs) -> list:
        """普通商品查询（按款）"""
        return self.paginated_call("/open/mall/item/query", kwargs)

    # -- 库存API --
    def query_inventory(self, **kwargs) -> list:
        """库存查询"""
        return self.paginated_call("/open/inventory/query", kwargs)

    # -- 订单API --
    def query_order(self, order_id: int = None, **kwargs) -> dict:
        """单笔订单查询"""
        params = dict(kwargs)
        if order_id:
            params["order_id"] = order_id
        return self.call("/open/orders/single/query", params)

    # -- 采购API --
    def query_purchase(self, **kwargs) -> list:
        """采购单查询"""
        return self.paginated_call("/open/purchase/query", kwargs)

    def query_supplier(self, **kwargs) -> list:
        """供应商查询"""
        return self.paginated_call("/open/supplier/query", kwargs)

    # -- WMS API（默认有权限） --
    def query_wms_partners(self, **kwargs) -> list:
        """仓库/物流查询"""
        return self.paginated_call("/open/wms/partner/query", kwargs)


# 全局单例
_client: Optional[JSTClient] = None


def get_client() -> JSTClient:
    global _client
    if _client is None:
        _client = JSTClient()
    return _client


# ============================================================
# 命令行入口
# ============================================================
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("聚水潭 API 客户端 — 连通性测试")
    print("=" * 60)
    print(f"  Host:         {os.getenv('JST_HOST', JSTClient.PRODUCTION_HOST)}")
    print(f"  App Key:      {os.getenv('JST_APP_KEY', '未设置')[:8]}***")
    print(f"  Access Token: {'已设置' if os.getenv('JST_ACCESS_TOKEN') else '未设置'}")

    try:
        client = get_client()
        print("✅ JSTClient 初始化成功")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    test_method = sys.argv[1] if len(sys.argv) > 1 else None

    if test_method:
        print(f"\n🚀 测试: {test_method}")
        try:
            data = client.call(test_method, {"page_index": 1, "page_size": 1})
            print(f"✅ 调用成功!")
            print(f"   {json.dumps(data, ensure_ascii=False)[:300]}")
        except JSTAPIError as e:
            print(f"❌ [{e.code}] {e.msg}")
            sys.exit(1)
    else:
        print()
        print("用法: python jst_client.py <api_path>")
        print("示例: python jst_client.py /open/shops/query")
        print()
        print("已确认接口（来自官方文档）:")
        print("  ✅ /open/shops/query        — 店铺列表")
        print("  ✅ /open/wms/partner/query  — 仓库/物流")
        print("  🔒 /open/sku/query          — 商品资料查询（需授权）")
        print("  🔒 /open/inventory/query    — 库存查询（需授权）")
        print("  🔒 /open/orders/single/query— 订单查询（需授权）")
        print("  🔒 /open/purchase/query     — 采购单查询（需授权）")
        print("  🔒 /open/supplier/query     — 供应商查询（需授权）")
