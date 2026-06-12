# jst-order-sync (alpha)

## 状态：🔵 Alpha

## 用途

订单同步与履约分析：发货时效、渠道对比、异常订单。

## 触发条件

- 用户说"订单情况"、"发货怎么样"、"履约分析"

## 执行

```python
from scripts.erp.jst_client import get_client
client = get_client()
orders = client.query_order()  # 按日期范围筛选
```

## 输出模板

```markdown
# 订单简报 YYYY-MM-DD
## 概览
- 今日新订单 / 今日发货 / 待发货
- 按渠道：1688 / 抖音 / 其他

## 履约
- 平均发货时效: X 小时
- 超时未发: N 单
- 异常订单: M 单
```
