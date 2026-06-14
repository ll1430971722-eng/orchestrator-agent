#!/usr/bin/env bash
# 初始化规划文件（task_plan.md + findings.md + progress.md）
# 用法: ./init-session.sh [任务名称]
# 文件放在项目根目录。

set -e

DATE=$(date +%Y-%m-%d)
PROJECT_NAME="${1:-任务}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# 从脚本位置往上 4 级到项目根目录: scripts/ → planning-with-files/ → skills/ → .claude/ → 项目根
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

echo "初始化规划文件: $PROJECT_NAME"

# --- task_plan.md ---
PLAN_FILE="$PROJECT_ROOT/task_plan.md"
if [ ! -f "$PLAN_FILE" ]; then
    cat > "$PLAN_FILE" << EOF
# 任务计划：$PROJECT_NAME

## 目标
[一句话说明要达成什么]

## 阶段进度

- [ ] Phase 1: 需求确认 — 状态: pending
- [ ] Phase 2: 方案设计 — 状态: pending
- [ ] Phase 3: 实施执行 — 状态: pending
- [ ] Phase 4: 验证与清理 — 状态: pending

## 决策记录

| 决策 | 原因 | 日期 |
|------|------|------|
| | | |

## 遇到的错误

| 错误 | 尝试次数 | 解决方案 |
|------|---------|---------|
| | | |

## 创建/修改的文件

| 文件 | 操作 | 阶段 |
|------|------|------|
| | | |
EOF
    echo "  ✅ 创建 $PLAN_FILE"
else
    echo "  ⏭️  $PLAN_FILE 已存在，跳过"
fi

# --- findings.md ---
FINDINGS_FILE="$PROJECT_ROOT/findings.md"
if [ ! -f "$FINDINGS_FILE" ]; then
    cat > "$FINDINGS_FILE" << 'EOF'
# 研究发现

## 需求分析
- 发现:
- 来源:
- 影响:

## 技术发现
- 发现:
- 来源:
- 影响:

## 风险与注意事项
- 发现:
- 来源:
- 影响:
EOF
    echo "  ✅ 创建 $FINDINGS_FILE"
else
    echo "  ⏭️  $FINDINGS_FILE 已存在，跳过"
fi

# --- progress.md ---
PROGRESS_FILE="$PROJECT_ROOT/progress.md"
if [ ! -f "$PROGRESS_FILE" ]; then
    cat > "$PROGRESS_FILE" << EOF
# 进度日志

## $DATE — 会话开始

### 开始
- 做了什么: 初始化规划文件
- 结果: task_plan.md + findings.md + progress.md 已创建
- 下一步: 进入 Phase 1 需求确认
EOF
    echo "  ✅ 创建 $PROGRESS_FILE"
else
    echo "  ⏭️  $PROGRESS_FILE 已存在，跳过"
fi

echo ""
echo "规划文件已就绪！"
echo "  📋 $PLAN_FILE"
echo "  🔍 $FINDINGS_FILE"
echo "  📝 $PROGRESS_FILE"
