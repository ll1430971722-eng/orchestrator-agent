---
description: 从抖店商家后台拉取完整运营数据（订单/商品/广告/售后/流量），保存到data/raw/目录。需要先登录。
disable-model-invocation: true
---
## 触发条件

当需要从抖店商家后台拉取运营数据时使用。会自动拉取订单、商品、广告、售后、流量数据。

## 功能

使用 Playwright MCP 依次导航到抖店后台各数据页面，提取结构化数据，保存到 `data/raw/` 目录。

## 前置条件

- 已登录抖店后台（如未登录，先执行 `douyin-login` 技能）
- `data/raw/` 目录存在

## 抖店后台页面 URL 映射

| 模块 | URL |
|------|-----|
| 订单管理 | `https://fxg.jinritemai.com/order/list` |
| 商品管理 | `https://fxg.jinritemai.com/product/list` |
| 售后管理 | `https://fxg.jinritemai.com/after-sale/refund/list` |
| 广告/推广 | `https://fxg.jinritemai.com/promotion/manage` |
| 流量/数据罗盘 | `https://fxg.jinritemai.com/data/overview` |

## 通用数据提取流程（每个模块都遵循）

### 进入页面
1. `browser_navigate` → 目标 URL
2. `browser_wait_for` 等待表格/数据加载（通常 2-3 秒）
3. `browser_screenshot` 截图留档

### 设置日期范围
1. `browser_snapshot` 识别日期选择器
2. `browser_click` 点击"近7天"（或指定日期）
3. 默认拉取最近 7 天数据

### 提取数据 — 核心方法
```
browser_evaluate 执行 JavaScript 提取页面数据：

// 通用表格提取
const rows = [];
document.querySelectorAll('table tbody tr').forEach(tr => {
  const row = {};
  tr.querySelectorAll('td').forEach((td, i) => {
    row[`col_${i}`] = td.innerText.trim();
  });
  if (Object.values(row).some(v => v)) rows.push(row);
});
return JSON.stringify(rows);
```

### 翻页处理
1. 检查是否有下一页按钮（.pagination .next:not(.disabled) 或包含"下一页"）
2. `browser_click` 点击下一页
3. 等待 1.5 秒
4. 重复提取直到无下一页或数据为空

---

## 模块 1: 订单数据 fetch-orders

**目标页面**: `https://fxg.jinritemai.com/order/list`

**提取字段**:
- 订单ID、订单状态、创建时间、支付时间
- 支付金额、订单金额
- 商品名称、SKU、数量
- 买家信息、物流状态、售后状态

**保存路径**: `data/raw/orders/YYYY-MM-DD/orders_raw.json`

**数据格式**:
```json
[
  {
    "order_id": "1234567890",
    "order_status": "已发货",
    "create_time": "2026-06-10 14:30:00",
    "pay_time": "2026-06-10 14:31:00",
    "pay_amount": 29.90,
    "product_name": "大容量笔袋",
    "sku_info": "蓝色款",
    "quantity": 1,
    "buyer_name": "张***",
    "after_sale_status": "无",
    "logistics_status": "已签收"
  }
]
```

**自检**: 提取 3 条后先验证字段映射是否正确，确认后再继续翻页。

---

## 模块 2: 商品数据 fetch-products

**目标页面**: `https://fxg.jinritemai.com/product/list`

**提取字段**:
- 商品ID、商品名称、售价、库存
- 状态（在售/下架/审核中）
- 近7日销量、近7日GMV
- 近7日访客数、转化率
- 评分、品类、创建时间

**保存路径**: `data/raw/products/YYYY-MM-DD/products_raw.json`

---

## 模块 3: 售后数据 fetch-after-sales

**目标页面**: `https://fxg.jinritemai.com/after-sale/refund/list`

**提取字段**:
- 售后单ID、关联订单ID
- 商品名称、退款金额、退款原因
- 售后状态（待处理/已退款/已拒绝）
- 创建时间、退款类型（仅退款/退货退款）

**保存路径**: `data/raw/after_sales/YYYY-MM-DD/after_sales_raw.json`

---

## 模块 4: 广告数据 fetch-ads

**目标页面**: `https://fxg.jinritemai.com/promotion/manage`

**提取字段**:
- 计划ID、计划名称
- 消耗、展示数、点击数、点击率
- 成交订单数、成交金额、ROI
- 状态（投放中/暂停）

**保存路径**: `data/raw/ads/YYYY-MM-DD/ads_raw.json`

**注意**: 如果店铺未开通广告投放，此页面可能无数据或不存在，记录为"无广告数据"即可。

---

## 模块 5: 流量数据 fetch-traffic

**目标页面**: `https://fxg.jinritemai.com/data/overview`

**提取方法**: 流量页面通常不是简单表格，而是图表+指标卡。

1. 先用 `browser_snapshot` 了解页面结构
2. `browser_evaluate` 提取指标卡数据：
   ```js
   const metrics = {};
   document.querySelectorAll('[class*="metric"], [class*="card"], [class*="statistic"]').forEach(el => {
     const label = el.querySelector('[class*="label"], [class*="title"]')?.innerText?.trim();
     const value = el.querySelector('[class*="value"], [class*="number"]')?.innerText?.trim();
     if (label && value) metrics[label] = value;
   });
   return JSON.stringify(metrics);
   ```
3. 如果有流量来源表格（搜索/推荐/直播/其他），同样提取
4. 提取不到结构化数据的，保存页面文本 + 截图作为兜底

**保存路径**: `data/raw/traffic/YYYY-MM-DD/traffic_raw.json`

---

## 输出汇总

执行完成后输出：

```
📊 数据拉取结果汇总
  ✅ 订单: 156 条 → data/raw/orders/YYYY-MM-DD/orders_raw.json
  ✅ 商品: 23 个 → data/raw/products/YYYY-MM-DD/products_raw.json
  ✅ 售后: 5 条  → data/raw/after_sales/YYYY-MM-DD/after_sales_raw.json
  ⚠️ 广告: 0 条（店铺未开通广告投放）
  ✅ 流量: 8 个指标 → data/raw/traffic/YYYY-MM-DD/traffic_raw.json

截图保存在 data/screenshots/

🔒 全程只读，未修改任何店铺数据
```

## 安全规则

- ✅ 只查看页面、提取数据、截图
- ❌ 不点击任何修改/操作按钮（编辑、删除、上架、下架、改价等）
- ❌ 不修改任何店铺数据
- 如果误触了修改按钮，立即取消，不提交任何修改
- 遇到弹窗或确认框，默认取消/关闭
