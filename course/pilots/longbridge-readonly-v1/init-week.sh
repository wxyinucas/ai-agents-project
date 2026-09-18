#!/usr/bin/env bash
set -eu

if [[ $# -ne 1 || ! "$1" =~ ^s[0-9]{2}$ ]]; then
  echo "用法：bash course/week-04/init-week.sh sXX"
  echo "示例：bash course/week-04/init-week.sh s07"
  exit 2
fi

student_id="$1"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
student_root="$repo_root/students/$student_id"
system_root="$student_root/system"
week_root="$student_root/weeks/week-04"

if [[ ! -d "$system_root" || ! -f "$system_root/pyproject.toml" || ! -f "$system_root/uv.lock" ]]; then
  echo "尚未找到可继续的 W3 system：students/$student_id/system"
  echo "请先完成 W3 ACCEPT，或使用教师在 W3 结束后提供的恢复基线。"
  exit 1
fi

if [[ -e "$week_root" ]]; then
  echo "目标已存在，未覆盖：students/$student_id/weeks/week-04"
  exit 1
fi

mkdir -p "$week_root"
cp "$script_dir/report-template.md" "$week_root/report.md"

echo "W4_INIT=PASS"
echo "student=$student_id"
echo "system=students/$student_id/system"
echo "report=students/$student_id/weeks/week-04/report.md"
