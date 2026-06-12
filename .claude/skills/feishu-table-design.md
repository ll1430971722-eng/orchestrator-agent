# 飞书多维表格设计 Skill

## 触发
当用户说"创建飞书表格"、"设计表格"、"表格美化"、"多维表格怎么做"、"飞书表格怎么设计得好看"时。

## 目标
让每一张飞书多维表格从诞生起就好看、好用，而不是建完再改。

---

## 核心原则

### 1. 数据库思维 > Excel 思维
- Excel 思路：一列一个属性 → 表越来越宽
- 多维表格思路：把信息拆成独立的**实体表**，用**关联字段**连接
- 一个实体一张表（商品表、订单表、问题表），不要全堆一起

### 2. 字段类型决定第一印象
别人看表第一眼不是看数据，是看**字段怎么显示的**——裸数字 vs 货币符号 vs 进度条 vs 星星，体验天差地别。

### 3. 视图即角色，视图即场景
一张表至少 2 个视图：**管理视图**（摘要）+ **数据视图**（全量）。不同人看不同视图，不用复制表。

---

## 字段类型决策树

### 金额/收入/成本 → `type: 2, ui_type: "Currency"`
```json
{"field_name": "GMV", "type": 2, "ui_type": "Currency",
 "property": {"decimal_places": 2, "use_separate": true}}
```
效果：¥1,234.56（自动千分位 + 人民币符号）

适用：GMV、客单价、广告消耗、退款金额、各渠道GMV

### 百分比/比率 → `type: 2, ui_type: "Progress"`
```json
{"field_name": "退款率", "type": 2, "ui_type": "Progress",
 "property": {"range": {"min": 0, "max": 1}}}
```
⚠️ 数据值必须在 0-1 范围（15.3% 存为 0.153，不是 15.3）

适用：退款率、转化率、点击率、占比、环比变化

### 评分/等级 → `type: 2, ui_type: "Rating"`
```json
{"field_name": "店铺评分", "type": 2, "ui_type": "Rating",
 "property": {"rating": {"max": 5, "icon": "star"}}}
```
效果：⭐⭐⭐⭐⭐ 可视评分

适用：店铺评分、商品体验分、物流分、服务分

### 状态/阶段 → `type: 3` (SingleSelect) + 颜色
```json
{"field_name": "优先级", "type": 3,
 "property": {"options": [
   {"name": "🔴 严重", "color": 1},
   {"name": "🟡 注意", "color": 2},
   {"name": "🟢 正常", "color": 3}
 ]}}
```
颜色码：0=灰, 1=红, 2=黄, 3=绿, 4=蓝, 5=紫

适用：优先级、状态、分类、渠道、负责人

### 自动计算 → `type: 20` (Formula)
```json
{"field_name": "退款健康度", "type": 20,
 "property": {"formula_expression": "IF([退款率] > 0.15, \"🔴 严重\", IF([退款率] > 0.08, \"🟡 注意\", \"🟢 健康\"))"}}
```
⚠️ 公式字段不支持跨表引用，最多 100 个公式字段

适用：环比、达成率、健康度判定、加权评分

### 日期 → `type: 5` (DateTime)
```json
{"field_name": "日期", "type": 5, "property": {"format": "yyyy-mm-dd"}}
```
⚠️ 写入值必须是 13 位毫秒时间戳

---

## 视图设计模式

### 规则：一张表≥2个视图

#### 视图1：「管理视图」— 给老板/决策者看
- **筛选**：近 7 天 / 本月至今
- **显示字段**：只展示核心指标（GMV、订单数、退款率、转化率、店铺评分），隐藏技术细节
- **排序**：按日期倒序
- **冻结**：首列（日期列）
- **类型**：Grid（表格）

#### 视图2：「运营全览」— 给运营/执行者看
- **筛选**：无（全量数据）
- **显示字段**：全部字段
- **排序**：按日期倒序
- **类型**：Grid（表格）

#### 视图3（追踪表专用）：「看板视图」— 按状态分组
- **类型**：Kanban
- **分组字段**：状态/优先级
- **卡片显示**：标题 + 负责人 + 截止日期

### 创建视图（API 调用示例）
```
feishu_create_bitable_view(app_token, table_id, "老板看板", "grid")
feishu_create_bitable_view(app_token, table_id, "看板视图", "kanban")
```

---

## 仪表盘（Dashboard）

### 现状
飞书 API 不支持直接创建空白仪表盘。只能：列出 + 复制已有仪表盘。

### 策略
1. 在飞书 UI 中手动创建一个「模板仪表盘」（包含：指标卡、趋势图、表格块）
2. 用 `feishu_copy_bitable_dashboard` 复制模板
3. 复制后手动调整数据源

### 仪表盘最小可行组件
| 组件 | 数据 | 位置 |
|------|------|------|
| 指标卡 | 今日GMV、订单数、退款率 | 顶部横排 |
| 折线图 | 近7天GMV趋势 | 中部左侧 |
| 柱状图 | 各渠道GMV占比 | 中部右侧 |
| 表格块 | 待处理问题TOP3 | 底部 |

---

## 表格命名规范

| 表类型 | 命名模式 | 示例 |
|--------|---------|------|
| 每日指标表 | [业务]每日指标 | 抖音每日指标 |
| 追踪表 | [业务]追踪 | 抖音每日问题追踪 |
| 明细表 | [业务]明细 | 抖音行动建议明细 |
| 概览表 | [业务]概览 | 每日运营概览 |

---

## 创建表格的完整流程

### Phase 1: 设计字段（先在纸上/对话中列出来）
1. 列出所有需要记录的信息
2. 按决策树确定每个字段的 type + ui_type
3. 金额 → Currency，百分比 → Progress，评分 → Rating，状态 → 单选+颜色

### Phase 2: 创建表
```
feishu_create_bitable_table(app_token, "表名", fields=[...])
```
在 fields 数组里直接用正确的 type/ui_type，不要建完再改。

### Phase 3: 写入数据
```
feishu_add_bitable_records(app_token, table_id, records=[...])
```
注意 Progress 字段值在 0-1 范围。

### Phase 4: 创建视图
```
feishu_create_bitable_view(app_token, table_id, "管理视图", "grid")
feishu_create_bitable_view(app_token, table_id, "看板视图", "kanban")
```

### Phase 5: 手动设置（API 不支持，需在 UI 操作）
- 条件格式/颜色规则（退款率>15%红色，转化率<1%红色）
- 仪表盘组件
- 高级权限
- 应用模式页面

---

## 常见错误与避免

| ❌ 错误做法 | ✅ 正确做法 |
|------------|-----------|
| 所有字段用 type=1（文本） | 金额用 Currency，比例用 Progress，状态用 SingleSelect |
| 百分比字段值存为 15.3 | Progress 字段值存为 0.153（0-1范围） |
| 一张表 80 个字段 | 拆成多张实体表，用关联字段连接 |
| 只建一个默认视图 | 至少建 2 个：管理视图 + 运营视图 |
| 状态字段用文本手写 | 用 SingleSelect + 颜色，只能选不能打错字 |
| 更新单选字段时只传新选项 | 必须传完整 options 列表（会覆盖） |
| 公式字段嵌套 10 层 IF | 拆成辅助字段分步计算 |
| 上手就建 20 张表 | MVP 先行：核心表 + 核心字段，跑通再扩展 |

---

## 现有飞书资源（orchestrator-agent）

| 资源 | ID |
|------|-----|
| Base | `GPFtbIOhCafB4HsANmVcbFOan4f` |
| 每日运营概览表 | `tbldtOCO6pR5g7bP` |
| 每日运营追踪表 | `tblLck1taVRaxldS` |
| 抖音每日指标表 | `tblK15Duu70dPX6G` |
| 抖音每日问题追踪表 | `tblOZGoovyt8qb0I` |
| 抖音行动建议明细表 | `tblPj7sBL74M07dN` |

---

## 相关工具速查

| 工具 | 功能 |
|------|------|
| `feishu_create_bitable_table` | 创建表（带字段定义） |
| `feishu_add_bitable_fields` | 新增字段（支持 Currency/Progress/Rating/Formula） |
| `feishu_update_bitable_fields` | 修改字段（改 ui_type、改选项颜色） |
| `feishu_list_bitable_fields` | 查看已有字段 |
| `feishu_list_bitable_views` | 查看已有视图 |
| `feishu_create_bitable_view` | 创建新视图（grid/kanban/gantt/gallery/form） |
| `feishu_update_bitable_view` | 更新视图（筛选/排序/显示字段） |
| `feishu_add_bitable_records` | 添加数据行 |
| `feishu_update_bitable_records` | 更新数据行 |
| `feishu_delete_bitable_records` | 删除数据行 |
| `feishu_list_bitable_dashboards` | 列出仪表盘 |
| `feishu_copy_bitable_dashboard` | 复制仪表盘模板 |
