---
description: 每日ERP数据同步：库存+订单+采购+商品，拉取后存到data/raw/erp/。聚水潭API对接。(alpha)
disable-model-invocation: true
---
## 状态：🔵 Alpha — API 客户端就绪，数据采集脚本待补齐

## 用途

每日 ERP 数据同步：库存 + 订单 + 采购 + 商品，拉取后存到 `data/raw/erp/`。

## 触发条件

- 用户说"同步ERP数据"、"今日供应链概览"
- orchestrator 每日分析流程 Phase 2 扩展

## 执行步骤

### Phase 1: 数据采集
```
python scripts/erp/fetch_inventory.py → data/raw/erp/inventory/YYYY-MM-DD/
python scripts/erp/fetch_orders.py → data/raw/erp/orders/YYYY-MM-DD/
python scripts/erp/fetch_products.py → data/raw/erp/products/YYYY-MM-DD/
python scripts/erp/fetch_procurement.py → data/raw/erp/procurement/YYYY-MM-DD/
```

### Phase 2: 分析
```
python scripts/erp/analyze_stock.py → 缺货/滞销/周转
python scripts/erp/analyze_orders.py → 履约/时效/渠道
```

### Phase 3: 报告
```
python scripts/erp/generate_reports.py → output/reports/erp/
```

## 数据纪律

**对接 API 时必须遵守五步验证**（详见 `memory/data-validation-rules.md`）：
1. 拆单条 — 拉 1 条确认所有字段
2. 三段验证 — 宽/窄/不可能范围
3. 逐日求和 = 总量
4. 日期格式验证
5. 与后台对齐

### 已验证的 API 行为

| API | 关键行为 |
|-----|---------|
| `/open/purchase/query` | 筛选 `modified` 字段；日期必须带时分秒；不支持按 `po_date` 筛选；≤7天 |
| `/open/inventory/query` | 筛选 `modified` 字段；≤7天 |
| `/open/orders/single/query` | 传时间参数 = 列表查询；≤7天 |
| `/open/sku/query` | 筛选 `modified` 字段；≤7天 |

## 依赖

- `scripts/erp/jst_client.py` — API 客户端
- `.env` 中配置 `JST_APP_KEY`, `JST_APP_SECRET`
