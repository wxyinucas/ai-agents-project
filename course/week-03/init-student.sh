#!/usr/bin/env bash
set -eu

if [[ $# -ne 1 || ! "$1" =~ ^s[0-9]{2}$ ]]; then
  echo "用法：bash course/week-03/init-student.sh sXX"
  echo "示例：bash course/week-03/init-student.sh s07"
  exit 2
fi

student_id="$1"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
student_root="$repo_root/students/$student_id"

if [[ -e "$student_root" ]]; then
  echo "目标已存在，未覆盖：students/$student_id"
  exit 1
fi

mkdir -p "$student_root/system" "$student_root/weeks/week-03"
cp "$script_dir/report-template.md" "$student_root/weeks/week-03/report.md"

echo "STUDENT_INIT=PASS"
echo "student=$student_id"
echo "system=students/$student_id/system"
echo "report=students/$student_id/weeks/week-03/report.md"
