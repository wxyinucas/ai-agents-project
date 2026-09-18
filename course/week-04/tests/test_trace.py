from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path.cwd().resolve()
W3 = Path(__file__).resolve().parents[2] / "week-03"
VALID_CSV = W3 / "tests" / "fixtures" / "another_valid_prices.csv"
MISSING_COLUMN_CSV = W3 / "tests" / "fixtures" / "missing_close.csv"


def run_market_check(path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    command = shutil.which("market-check")
    assert command is not None, "找不到 market-check 命令"
    return subprocess.run(
        [command, str(path), *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def trace_lines(completed: subprocess.CompletedProcess[str]) -> list[str]:
    return [line for line in completed.stderr.splitlines() if line.strip()]


def test_trace_is_optional_and_does_not_change_the_result() -> None:
    normal = run_market_check(VALID_CSV)
    traced = run_market_check(VALID_CSV, "--trace")
    lines = trace_lines(traced)

    assert normal.returncode == traced.returncode == 0
    assert normal.stdout == traced.stdout
    assert normal.stderr == "", "不开启 --trace 时不应出现诊断信息"
    assert len(lines) == 2, traced.stderr
    assert str(VALID_CSV) in lines[0]
    assert re.search(r"(?<!\d)3(?!\d)", lines[1]), lines[1]
    assert "timestamp,symbol,close" not in traced.stderr


def test_missing_file_stops_after_the_first_trace(tmp_path: Path) -> None:
    path = tmp_path / "does-not-exist.csv"
    normal = run_market_check(path)
    traced = run_market_check(path, "--trace")
    lines = trace_lines(traced)

    assert traced.returncode != 0
    assert traced.returncode == normal.returncode
    assert traced.stdout == normal.stdout
    assert "DATA_CHECK=FAIL" in traced.stdout + traced.stderr
    assert len(lines) == 1, traced.stderr
    assert str(path) in lines[0]


def test_loaded_file_can_still_fail_its_contract() -> None:
    normal = run_market_check(MISSING_COLUMN_CSV)
    traced = run_market_check(MISSING_COLUMN_CSV, "--trace")
    lines = trace_lines(traced)

    assert traced.returncode != 0
    assert traced.returncode == normal.returncode
    assert traced.stdout == normal.stdout
    assert "DATA_CHECK=FAIL" in traced.stdout + traced.stderr
    assert len(lines) == 2, traced.stderr
    assert str(MISSING_COLUMN_CSV) in lines[0]
    assert re.search(r"(?<!\d)2(?!\d)", lines[1]), lines[1]
