#!/usr/bin/env bash
# 检查 task_plan.md 中所有阶段的完成状态
# 用法: ./check-complete.sh [task_plan.md 路径]
# 默认查找项目根目录的 task_plan.md

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# 从脚本位置往上 4 级到项目根目录: scripts/ → planning-with-files/ → skills/ → .claude/ → 项目根
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
PLAN_FILE="${1:-$PROJECT_ROOT/task_plan.md}"

if [ ! -f "$PLAN_FILE" ]; then
    echo "[planning-with-files] 未找到 task_plan.md — 没有活跃的规划会话。"
    exit 0
fi

python3 << PYEOF
import re, sys

with open("$PLAN_FILE", "r") as f:
    content = f.read()

# Count phases: lines starting with "- [ ]" or "- [x]" that contain "Phase"
phase_lines = re.findall(r'^- \[(.)\].*Phase', content, re.MULTILINE)
total = len(phase_lines)
complete = sum(1 for m in phase_lines if m == 'x')
in_progress = len(re.findall(r'状态: in_progress', content))
pending = len(re.findall(r'状态: pending', content))

if total == 0:
    print("[planning-with-files] 📋 task_plan.md 存在但未检测到阶段")
elif complete == total:
    print(f"[planning-with-files] ✅ 全部阶段完成 ({complete}/{total})")
else:
    print(f"[planning-with-files] 🔄 进行中 ({complete}/{total} 完成)")
    if in_progress > 0:
        print(f"[planning-with-files]    → {in_progress} 个阶段执行中")
    if pending > 0:
        print(f"[planning-with-files]    → {pending} 个阶段待处理")

# Show phase status details
print()
print("--- 阶段状态明细 ---")
for line in content.split('\n'):
    if re.match(r'^- \[.?\].*Phase', line):
        print(line)
PYEOF
