import pytest

from yoga_relief.models import Answers
from yoga_relief.triage import should_seek_medical


@pytest.mark.parametrize(
    ("severity", "duration", "cause", "expected"),
    [
        ("severe", "month_plus", "unknown", True),       # 規則 1
        ("severe", "month_plus", "injury", True),        # 規則 1 與 2 重疊
        ("moderate", "today", "injury", True),           # 規則 2
        ("severe", "days", "injury", True),              # 規則 2
        ("mild", "today", "injury", False),              # injury 但只有 mild
        ("moderate", "month_plus", "sedentary", False),  # month_plus 但非 severe
        ("severe", "week_plus", "exertion", False),      # severe 但不到一個月
        ("mild", "today", "unknown", False),
    ],
)
def test_should_seek_medical(severity, duration, cause, expected):
    answers = Answers(severity=severity, duration=duration, cause=cause)
    assert should_seek_medical(answers) is expected
