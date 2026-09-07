from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tomllib


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_market_check(path: Path) -> subprocess.CompletedProcess[str]:
    command = shutil.which("market-check")
    assert command is not None, (
        "找不到 market-check 命令；请在 pyproject.toml 中注册项目命令"
    )

    return subprocess.run(
        [command, str(path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def parse_key_value_output(output: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def assert_report_contains(
    actual: dict[str, str], expected: dict[str, str]
) -> None:
    for key, value in expected.items():
        assert actual.get(key) == value, f"{key} 应为 {value!r}，实际为 {actual.get(key)!r}"


def test_uv_project_declares_required_environment() -> None:
    pyproject_path = ROOT / "pyproject.toml"
    lock_path = ROOT / "uv.lock"

    assert pyproject_path.is_file(), "缺少 pyproject.toml"
    assert lock_path.is_file(), "缺少 uv.lock"

    with pyproject_path.open("rb") as handle:
        pyproject = tomllib.load(handle)

    project = pyproject.get("project", {})
    assert project.get("name") == "quant-lab"
    assert project.get("requires-python") == ">=3.12,<3.13"

    dependencies = [str(item).lower() for item in project.get("dependencies", [])]
    dev_dependencies = [
        str(item).lower()
        for item in pyproject.get("dependency-groups", {}).get("dev", [])
    ]
    assert any(item.startswith("pandas") for item in dependencies)
    assert any(item.startswith("pytest") for item in dev_dependencies)


def test_sample_fixture_reports_visible_facts() -> None:
    completed = run_market_check(ROOT / "data" / "sample_prices.csv")
    facts = parse_key_value_output(completed.stdout)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert_report_contains(
        facts,
        {
            "execution_mode": "fixture",
            "symbols": "AAPL",
            "rows": "4",
            "start": "2026-09-01T09:30:00",
            "end": "2026-09-01T09:33:00",
            "DATA_CHECK": "PASS",
        },
    )


def test_another_valid_fixture_is_not_hard_coded() -> None:
    completed = run_market_check(FIXTURES / "another_valid_prices.csv")
    facts = parse_key_value_output(completed.stdout)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert_report_contains(
        facts,
        {
            "execution_mode": "fixture",
            "symbols": "MSFT,TSLA",
            "rows": "3",
            "start": "2026-09-02T09:30:00",
            "end": "2026-09-02T09:32:00",
            "DATA_CHECK": "PASS",
        },
    )


def test_missing_required_column_fails_clearly() -> None:
    completed = run_market_check(FIXTURES / "missing_close.csv")

    assert completed.returncode != 0
    assert "DATA_CHECK=FAIL" in completed.stdout + completed.stderr


def test_missing_file_fails_clearly(tmp_path: Path) -> None:
    completed = run_market_check(tmp_path / "does-not-exist.csv")

    assert completed.returncode != 0
    assert "DATA_CHECK=FAIL" in completed.stdout + completed.stderr
