import pytest

from database import normalize_issue_status_group


@pytest.mark.parametrize(
    "value,expected",
    [
        ("open", "Active"),
        ("in_progress", "Active"),
        ("reopened", "Active"),
        ("pending", "Active"),
        ("on_hold", "Active"),
        ("closed", "Closed"),
        ("completed", "Closed"),
        ("resolved", "Closed"),
        ("", "Other"),
        (None, "Other"),
        ("unknown_status", "Other"),
    ],
)
def test_normalize_issue_status_group(value, expected):
    assert normalize_issue_status_group(value) == expected
