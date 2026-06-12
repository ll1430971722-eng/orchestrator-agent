"""
飞书 API 统一客户端（MCP Server 专用）
从项目根目录的 .env 加载凭证，支持所有飞书 API 端点。
"""

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from dotenv import load_dotenv

# 从项目根目录加载 .env
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class FeishuAPIError(Exception):
    """飞书 API 错误"""
    def __init__(self, code: int, msg: str, raw: dict = None):
        self.code = code
        self.msg = msg
        self.raw = raw or {}
        super().__init__(f"飞书 API 错误 [{code}]: {msg}")


class FeishuClient:
    """飞书开放平台 API 客户端"""

    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self._tenant_token: Optional[str] = None
        self._token_expire_at: float = 0
        self._last_request_at: float = 0
        self._min_interval: float = 0.1

        if not self.app_id or not self.app_secret:
            raise ValueError(
                "FEISHU_APP_ID 和 FEISHU_APP_SECRET 未设置。"
                "请在 feishu-agent/.env 文件中配置。"
            )

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_at
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

    def _get_tenant_token(self) -> str:
        if self._tenant_token and time.time() < self._token_expire_at - 60:
            return self._tenant_token

        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal"
        resp = requests.post(
            url,
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise FeishuAPIError(
                data.get("code", -1),
                f"获取 tenant_access_token 失败: {data.get('msg', '未知错误')}"
            )

        self._tenant_token = data["tenant_access_token"]
        self._token_expire_at = time.time() + data.get("expire", 7200)
        return self._tenant_token

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_tenant_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        json_body: Optional[Dict] = None,
        retries: int = 2,
    ) -> Dict[str, Any]:
        """统一请求方法"""
        self._rate_limit()
        url = f"{self.BASE_URL}{path}"

        for attempt in range(retries + 1):
            try:
                resp = requests.request(
                    method=method, url=url, headers=self._headers(),
                    params=params, json=json_body, timeout=30,
                )
                self._last_request_at = time.time()
                # Parse JSON first — Feishu returns error codes in body even on HTTP 4xx
                try:
                    data = resp.json()
                except Exception:
                    resp.raise_for_status()
                    raise  # won't reach here if raise_for_status succeeds
                code = data.get("code", -1)

                if code == 0:
                    return data

                # token 过期重试
                if code in (99991663, 99991664, 99991665):
                    self._tenant_token = None
                    if attempt < retries:
                        continue

                raise FeishuAPIError(code, data.get("msg", "未知错误"), data)

            except requests.RequestException as e:
                if attempt < retries:
                    time.sleep(1 * (attempt + 1))
                    continue
                raise FeishuAPIError(-1, f"网络请求失败: {e}")

        raise FeishuAPIError(-1, "重试次数已用完")

    # ---- Convenience methods ----

    def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        return self.request("GET", path, params=params)

    def post(self, path: str, json_body: Optional[Dict] = None) -> Dict[str, Any]:
        return self.request("POST", path, json_body=json_body)

    def patch(self, path: str, json_body: Optional[Dict] = None) -> Dict[str, Any]:
        return self.request("PATCH", path, json_body=json_body)

    def put(self, path: str, json_body: Optional[Dict] = None) -> Dict[str, Any]:
        return self.request("PUT", path, json_body=json_body)

    def delete(self, path: str) -> Dict[str, Any]:
        return self.request("DELETE", path)

    def paginated_get(
        self, path: str, params: Optional[Dict] = None,
        item_key: str = "items", max_pages: int = 50,
    ) -> list:
        """通用分页 GET 请求"""
        items = []
        page_token = None
        pages = 0
        base_params = (params or {}).copy()

        while pages < max_pages:
            p = {**base_params, "page_size": base_params.get("page_size", 500)}
            if page_token:
                p["page_token"] = page_token
            resp = self.get(path, params=p)
            data = resp.get("data", {})
            items.extend(data.get(item_key, []))
            page_token = data.get("page_token") or data.get("has_more") and self._extract_page_token(data)
            pages += 1
            if not page_token:
                break

        return items

    @staticmethod
    def _extract_page_token(data: dict) -> Optional[str]:
        return data.get("page_token")


# 全局单例
_client: Optional[FeishuClient] = None


def get_client() -> FeishuClient:
    global _client
    if _client is None:
        _client = FeishuClient()
    return _client
