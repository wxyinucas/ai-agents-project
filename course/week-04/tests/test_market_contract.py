from __future__ import annotations

from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tomllib

import pytest


ROOT = Path.cwd().resolve()
COURSE_WEEK = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID_REPLAY = COURSE_WEEK / "data" / "synthetic-replay.json"
EXPECTED_QUERY = {
    "symbol": "AAPL.US",
    "period": "day",
    "adjustment": "none",
    "start_date": "2025-01-02",
    "end_date": "2025-01-10",
    "market_timezone": "America/New_York",
}
EXPECTED_SESSION_DATES = {
    "2025-01-02",
    "2025-01-03",
    "2025-01-06",
    "2025-01-07",
    "2025-01-08",
    "2025-01-10",
}
BUSINESS_BAR_FIELDS = (
    "symbol",
    "session_date",
    "market_timezone",
    "event_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
)
PRICE_FIELDS = ("open", "high", "low", "close")


def run_market_observe(
    path: Path, *, extra_environment: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    command = shutil.which("market-observe")
    assert command is not None, (
        "找不到 market-observe 命令；请在现有 pyproject.toml 中注册项目命令"
    )

    environment = os.environ.copy()
    if extra_environment:
        environment.update(extra_environment)

    return subprocess.run(
        [command, str(path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def combined_output(completed: subprocess.CompletedProcess[str]) -> str:
    return completed.stdout + completed.stderr


def parse_key_value_output(output: str) -> dict[str, str]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    assert all(line.count("=") == 1 for line in lines), (
        f"证据必须全部使用单一 key=value 行，实际为：{output!r}"
    )

    pairs = [line.split("=", 1) for line in lines]
    keys = [key.strip() for key, _ in pairs]
    assert all(keys), "证据行的 key 不得为空"
    assert len(keys) == len(set(keys)), "同一个证据 key 不得重复输出"
    return {key.strip(): value.strip() for key, value in pairs}


def normalize_decimal(value: str) -> str:
    number = Decimal(value)
    assert number.is_finite()
    if number == 0:
        return "0"
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def expected_data_sha256(document: dict[str, object]) -> str:
    raw_bars = document["bars"]
    assert isinstance(raw_bars, list)
    bars: list[dict[str, object]] = []
    for raw_bar in raw_bars:
        assert isinstance(raw_bar, dict)
        bar = {field: raw_bar[field] for field in BUSINESS_BAR_FIELDS}
        for field in PRICE_FIELDS:
            bar[field] = normalize_decimal(str(bar[field]))
        bars.append(bar)
    bars.sort(key=lambda bar: (str(bar["symbol"]), str(bar["event_time"])))

    payload = {"query": EXPECTED_QUERY, "bars": bars}
    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def load_document(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def test_uv_project_uses_teacher_owned_common_package() -> None:
    pyproject_path = ROOT / "pyproject.toml"
    with pyproject_path.open("rb") as handle:
        pyproject = tomllib.load(handle)

    project_dependencies = [
        str(item).lower() for item in pyproject["project"]["dependencies"]
    ]
    dependency_groups = pyproject.get("dependency-groups", {})
    all_dependencies = project_dependencies + [
        str(item).lower()
        for group in dependency_groups.values()
        for item in group
    ]
    assert any(item == "course-common" for item in project_dependencies), (
        "[project].dependencies 必须增加 course-common"
    )
    assert not any(
        "longbridge" in item or "longport" in item for item in all_dependencies
    ), "学生 system 不得安装 Longbridge SDK"

    source = pyproject.get("tool", {}).get("uv", {}).get("sources", {}).get(
        "course-common"
    )
    assert isinstance(source, dict), "[tool.uv.sources] 缺少 course-common"
    assert source.get("path") == "../../../common", (
        "course-common 必须指向 ../../../common，不要复制公共实现"
    )
    assert source.get("editable") is True, "course-common 的本地来源必须设置 editable=true"


def test_course_query_and_replay_fixture_agree() -> None:
    query = load_document(COURSE_WEEK / "query.json")
    replay = load_document(VALID_REPLAY)
    bars = replay["bars"]
    assert isinstance(bars, list)

    assert query == EXPECTED_QUERY
    assert replay["query"] == EXPECTED_QUERY
    assert replay["execution_mode"] == "replay"
    assert replay["platform_called"] is False
    assert replay["source"] == "course_synthetic_fixture"
    assert replay["account_mode"] == "not_applicable"
    assert "SYNTHETIC" in str(replay.get("fixture_notice", ""))
    assert len(bars) == 6
    assert {str(bar["session_date"]) for bar in bars} == EXPECTED_SESSION_DATES
    assert all(bar["available_at"] == replay["as_of"] for bar in bars)


def test_valid_replay_reports_sanitized_evidence() -> None:
    document = load_document(VALID_REPLAY)
    completed = run_market_observe(VALID_REPLAY)
    output = combined_output(completed)
    facts = parse_key_value_output(output)

    assert completed.returncode == 0, output
    expected = {
        "schema_version": "course.market-bars.v1",
        "execution_mode": "replay",
        "platform_called": "false",
        "source": "course_synthetic_fixture",
        "account_mode": "not_applicable",
        "symbol": "AAPL.US",
        "period": "day",
        "adjustment": "none",
        "market_timezone": "America/New_York",
        "query_start_date": "2025-01-02",
        "query_end_date": "2025-01-10",
        "as_of": "2025-01-11T02:00:00Z",
        "rows": "6",
        "first_session": "2025-01-02",
        "last_session": "2025-01-10",
        "data_sha256": expected_data_sha256(document),
        "MARKET_CONTRACT": "PASS",
    }
    for key, value in expected.items():
        assert facts.get(key) == value, (
            f"{key} 应为 {value!r}，实际为 {facts.get(key)!r}"
        )
    assert "SYNTHETIC TEACHING VALUES" not in output
    assert '"open"' not in output


def test_hash_is_independent_of_order_and_observation_metadata() -> None:
    changed = FIXTURES / "synthetic-replay-reordered.json"
    first = run_market_observe(VALID_REPLAY)
    second = run_market_observe(changed)
    first_facts = parse_key_value_output(combined_output(first))
    second_facts = parse_key_value_output(combined_output(second))

    assert first.returncode == second.returncode == 0
    assert first_facts["data_sha256"] == second_facts["data_sha256"]
    assert first_facts["as_of"] != second_facts["as_of"]
    assert "W4_PRIVATE_MARKER_2E4C" not in combined_output(second)


def test_longbridge_readonly_envelope_has_the_same_business_hash(
    tmp_path: Path,
) -> None:
    # This checks the declared envelope shape only; it is not evidence of an API call.
    document = load_document(FIXTURES / "synthetic-replay-reordered.json")
    document["execution_mode"] = "longbridge_readonly"
    document["platform_called"] = True
    document["source"] = "longbridge"
    document["account_mode"] = "paper"
    specimen = tmp_path / "longbridge-contract-shape-only.json"
    specimen.write_text(json.dumps(document), encoding="utf-8")

    replay = run_market_observe(VALID_REPLAY)
    candidate = run_market_observe(specimen)
    replay_facts = parse_key_value_output(combined_output(replay))
    candidate_facts = parse_key_value_output(combined_output(candidate))

    assert candidate.returncode == 0, combined_output(candidate)
    assert candidate_facts["execution_mode"] == "longbridge_readonly"
    assert candidate_facts["platform_called"] == "true"
    assert candidate_facts["source"] == "longbridge"
    assert candidate_facts["account_mode"] == "paper"
    assert candidate_facts["data_sha256"] == replay_facts["data_sha256"]


@pytest.mark.parametrize(
    ("fixture_name", "reason_code"),
    [
        ("missing-field.json", "missing_field"),
        ("duplicate-bar.json", "duplicate_bar"),
        ("ohlc-violation.json", "ohlc_violation"),
        ("time-boundary.json", "time_boundary"),
        ("non-midnight-event.json", "time_boundary"),
        ("mode-source-conflict.json", "mode_source_conflict"),
        ("wrong-query.json", "invalid_query"),
        ("invalid-value.json", "invalid_value"),
        ("invalid-volume.json", "invalid_value"),
        ("missing-session.json", "session_coverage"),
        ("sensitive-field.json", "sensitive_field"),
    ],
)
def test_invalid_documents_fail_without_echo(
    fixture_name: str, reason_code: str
) -> None:
    completed = run_market_observe(FIXTURES / fixture_name)
    output = combined_output(completed)
    facts = parse_key_value_output(output)

    assert completed.returncode != 0
    assert facts == {
        "reason_code": reason_code,
        "MARKET_CONTRACT": "FAIL",
    }
    assert "W4_PRIVATE_MARKER_2E4C" not in output
    assert "Traceback" not in output


def test_missing_file_fails_without_echoing_its_path(tmp_path: Path) -> None:
    secret_marker = "W4_PRIVATE_MARKER_2E4C"
    missing = tmp_path / f"{secret_marker}.json"
    completed = run_market_observe(missing)
    output = combined_output(completed)

    assert completed.returncode != 0
    assert parse_key_value_output(output) == {
        "reason_code": "file_not_found",
        "MARKET_CONTRACT": "FAIL",
    }
    assert secret_marker not in output


def test_invalid_json_fails_without_echoing_contents(tmp_path: Path) -> None:
    secret_marker = "W4_PRIVATE_MARKER_2E4C"
    malformed = tmp_path / "malformed.json"
    malformed.write_text(f'{{"private": "{secret_marker}"', encoding="utf-8")
    completed = run_market_observe(malformed)
    output = combined_output(completed)

    assert completed.returncode != 0
    assert parse_key_value_output(output) == {
        "reason_code": "invalid_json",
        "MARKET_CONTRACT": "FAIL",
    }
    assert secret_marker not in output


def test_environment_secrets_are_neither_needed_nor_reported() -> None:
    secret_marker = "W4_PRIVATE_MARKER_2E4C"
    completed = run_market_observe(
        VALID_REPLAY,
        extra_environment={
            "LONGBRIDGE_APP_KEY": secret_marker,
            "LONGBRIDGE_APP_SECRET": secret_marker,
            "LONGBRIDGE_ACCESS_TOKEN": secret_marker,
        },
    )
    output = combined_output(completed)

    assert completed.returncode == 0, output
    assert parse_key_value_output(output)["MARKET_CONTRACT"] == "PASS"
    assert secret_marker not in output
    assert re.search(r"(?m)^data_sha256=[0-9a-f]{64}$", output)
