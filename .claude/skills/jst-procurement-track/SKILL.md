---
description: ERP采购进度追踪：采购单状态、交期预警、供应商分析。基于聚水潭API。(alpha)
disable-model-invocation: true
---
## 状态：🔵 Alpha

## 用途

采购进度追踪：采购单状态、交期预警、供应商分析。

## 触发条件

- 用户说"采购进度"、"采购单怎么样了"、"供应商情况"

## 执行

```python
from scripts.erp.jst_client import get_client
client = get_client()
purchases = client.query_purchase()
```

## 输出模板

```markdown
# 采购进度 YYYY-MM-DD
## 概览
- 进行中采购单: N
- 超期未入库: M
- 预计近日到货: K

## 🔴 交期预警
| 采购单号 | 供应商 | 预计交期 | 超期天数 |
```
