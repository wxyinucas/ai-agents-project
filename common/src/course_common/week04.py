"""Read and verify the small market-data contract introduced in W4."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from zoneinfo import ZoneInfo


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
TOP_LEVEL_FIELDS = {
    "schema_version",
    "execution_mode",
    "platform_called",
    "source",
    "account_mode",
    "query",
    "as_of",
    "bars",
}
BAR_FIELDS = {
    "symbol",
    "session_date",
    "market_timezone",
    "event_time",
    "available_at",
    "open",
    "high",
    "low",
    "close",
    "volume",
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
UTC_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "apikey",
    "appkey",
    "accountid",
)


@dataclass(frozen=True)
class MarketObservation:
    """A safe result whose lines may be printed or copied into a report."""

    exit_code: int
    evidence_lines: tuple[str, ...]


class _ContractError(Exception):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def _failure(reason_code: str) -> MarketObservation:
    return MarketObservation(
        exit_code=1,
        evidence_lines=(
            f"reason_code={reason_code}",
            "MARKET_CONTRACT=FAIL",
        ),
    )


def _require_fields(value: dict[str, Any], required: set[str]) -> None:
    if required.difference(value):
        raise _ContractError("missing_field")


def _contains_sensitive_field(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            compact_key = re.sub(r"[^a-z0-9]", "", key.casefold())
            if any(part in compact_key for part in SENSITIVE_KEY_PARTS):
                return True
            if _contains_sensitive_field(child):
                return True
    elif isinstance(value, list):
        return any(_contains_sensitive_field(child) for child in value)
    return False


def _parse_utc(value: Any) -> datetime:
    if not isinstance(value, str) or UTC_TIMESTAMP.fullmatch(value) is None:
        raise _ContractError("invalid_value")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise _ContractError("invalid_value") from error
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise _ContractError("invalid_value")
    return parsed


def _parse_decimal_string(value: Any) -> Decimal:
    if not isinstance(value, str):
        raise _ContractError("invalid_value")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise _ContractError("invalid_value") from error
    if not number.is_finite():
        raise _ContractError("invalid_value")
    return number


def _normalize_decimal(number: Decimal) -> str:
    if number == 0:
        return "0"
    text = format(number, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _validate_bar(raw_bar: Any, as_of: datetime) -> dict[str, Any]:
    if not isinstance(raw_bar, dict):
        raise _ContractError("invalid_value")
    _require_fields(raw_bar, BAR_FIELDS)

    if raw_bar["symbol"] != EXPECTED_QUERY["symbol"]:
        raise _ContractError("invalid_value")
    if raw_bar["market_timezone"] != EXPECTED_QUERY["market_timezone"]:
        raise _ContractError("invalid_value")

    event_time = _parse_utc(raw_bar["event_time"])
    available_at = _parse_utc(raw_bar["available_at"])
    try:
        session_date = date.fromisoformat(raw_bar["session_date"])
    except (TypeError, ValueError) as error:
        raise _ContractError("invalid_value") from error

    market_time = event_time.astimezone(ZoneInfo(EXPECTED_QUERY["market_timezone"]))
    query_start = date.fromisoformat(EXPECTED_QUERY["start_date"])
    query_end = date.fromisoformat(EXPECTED_QUERY["end_date"])
    if (
        session_date != market_time.date()
        or market_time.time() != datetime.min.time()
        or not query_start <= session_date <= query_end
        or available_at != as_of
        or event_time > available_at
    ):
        raise _ContractError("time_boundary")

    numbers = {
        field: _parse_decimal_string(raw_bar[field]) for field in PRICE_FIELDS
    }
    volume = raw_bar["volume"]
    if (
        isinstance(volume, bool)
        or not isinstance(volume, int)
        or volume < 0
        or any(value <= 0 for value in numbers.values())
    ):
        raise _ContractError("invalid_value")

    if (
        numbers["high"] < max(numbers.values())
        or numbers["low"] > min(numbers.values())
    ):
        raise _ContractError("ohlc_violation")

    return {**raw_bar, "_numbers": numbers}


def _data_sha256(bars: list[dict[str, Any]]) -> str:
    canonical_bars: list[dict[str, Any]] = []
    for bar in bars:
        canonical = {field: bar[field] for field in BUSINESS_BAR_FIELDS}
        for field, number in bar["_numbers"].items():
            canonical[field] = _normalize_decimal(number)
        canonical_bars.append(canonical)

    payload = {"query": EXPECTED_QUERY, "bars": canonical_bars}
    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def observe_market_file(path: str | Path) -> MarketObservation:
    """Return sanitized evidence for a local course.market-bars.v1 document."""

    input_path = Path(path)
    if not input_path.is_file():
        return _failure("file_not_found")
    try:
        document = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return _failure("invalid_json")

    try:
        if not isinstance(document, dict):
            raise _ContractError("invalid_schema")
        if _contains_sensitive_field(document):
            raise _ContractError("sensitive_field")
        _require_fields(document, TOP_LEVEL_FIELDS)
        if document["schema_version"] != "course.market-bars.v1":
            raise _ContractError("invalid_schema")
        if not isinstance(document["platform_called"], bool):
            raise _ContractError("mode_source_conflict")

        provenance = (
            document["execution_mode"],
            document["platform_called"],
            document["source"],
            document["account_mode"],
        )
        if provenance not in {
            ("replay", False, "course_synthetic_fixture", "not_applicable"),
            ("longbridge_readonly", True, "longbridge", "paper"),
        }:
            raise _ContractError("mode_source_conflict")

        if document["query"] != EXPECTED_QUERY:
            raise _ContractError("invalid_query")
        as_of = _parse_utc(document["as_of"])
        raw_bars = document["bars"]
        if not isinstance(raw_bars, list) or not raw_bars:
            raise _ContractError("invalid_value")

        bars = [_validate_bar(raw_bar, as_of) for raw_bar in raw_bars]
        bars.sort(key=lambda bar: (bar["symbol"], bar["event_time"]))
        keys = [(bar["symbol"], bar["event_time"]) for bar in bars]
        if len(keys) != len(set(keys)):
            raise _ContractError("duplicate_bar")
        if {bar["session_date"] for bar in bars} != EXPECTED_SESSION_DATES:
            raise _ContractError("session_coverage")
    except _ContractError as error:
        return _failure(error.reason_code)
    except Exception:
        return _failure("invalid_schema")

    evidence = {
        "schema_version": document["schema_version"],
        "execution_mode": document["execution_mode"],
        "platform_called": str(document["platform_called"]).lower(),
        "source": document["source"],
        "account_mode": document["account_mode"],
        "symbol": EXPECTED_QUERY["symbol"],
        "period": EXPECTED_QUERY["period"],
        "adjustment": EXPECTED_QUERY["adjustment"],
        "market_timezone": EXPECTED_QUERY["market_timezone"],
        "query_start_date": EXPECTED_QUERY["start_date"],
        "query_end_date": EXPECTED_QUERY["end_date"],
        "as_of": document["as_of"],
        "rows": str(len(bars)),
        "first_session": bars[0]["session_date"],
        "last_session": bars[-1]["session_date"],
        "data_sha256": _data_sha256(bars),
        "MARKET_CONTRACT": "PASS",
    }
    return MarketObservation(
        exit_code=0,
        evidence_lines=tuple(f"{key}={value}" for key, value in evidence.items()),
    )
