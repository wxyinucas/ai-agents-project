"""Collect the five public W3 checks as part of every W4 test run."""

from __future__ import annotations

import importlib.util
from pathlib import Path


W3_TEST_FILE = Path(__file__).resolve().parents[2] / "week-03" / "tests" / "test_project_contract.py"
SPEC = importlib.util.spec_from_file_location("_week03_project_contract", W3_TEST_FILE)
assert SPEC is not None and SPEC.loader is not None
W3 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(W3)


test_w3_uv_project_declares_required_environment = (
    W3.test_uv_project_declares_required_environment
)
test_w3_sample_fixture_reports_visible_facts = (
    W3.test_sample_fixture_reports_visible_facts
)
test_w3_another_valid_fixture_is_not_hard_coded = (
    W3.test_another_valid_fixture_is_not_hard_coded
)
test_w3_missing_required_column_fails_clearly = (
    W3.test_missing_required_column_fails_clearly
)
test_w3_missing_file_fails_clearly = W3.test_missing_file_fails_clearly
