# jst-inventory-check (alpha)

## 状态：🔵 Alpha

## 用途

快速查看库存健康度：缺货预警、滞销品、周转天数。

## 触发条件

- 用户说"看下库存"、"库存怎么样"、"缺货了吗"

## 执行

```python
from scripts.erp.jst_client import get_client
client = get_client()
inventory = client.query_inventory()
```

然后分析：
- 总 SKU 数 / 有库存 SKU 数
- 🔴 缺货 SKU（库存 = 0 或低于安全线）
- 🟡 滞销品（最近 30 天无销售但有库存）
- 库存周转天数估算

## 输出模板

```markdown
# 库存快照 YYYY-MM-DD
- 总 SKU: N / 有库存: M
- 缺货预警: N 个 SKU
- 滞销预警: M 个 SKU
- 预估周转: X 天
```
