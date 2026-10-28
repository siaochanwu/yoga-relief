import pytest
from pydantic import ValidationError

from yoga_relief.models import (
    CAUSE_LABELS,
    DURATION_LABELS,
    SEVERITY_LABELS,
    AdviceRequest,
    Answers,
    BodyPart,
    Cause,
    Duration,
    Intensity,
    Pose,
    Severity,
    View,
)


def test_enum_values_are_wire_strings():
    assert Severity.MILD == "mild"
    assert Duration.MONTH_PLUS == "month_plus"
    assert Cause.INJURY == "injury"
    assert Intensity.GENTLE == "gentle"
    assert View.BACK == "back"
    assert f"{Severity.SEVERE}" == "severe"


def test_every_enum_member_has_a_label():
    assert set(SEVERITY_LABELS) == set(Severity)
    assert set(DURATION_LABELS) == set(Duration)
    assert set(CAUSE_LABELS) == set(Cause)


def test_pose_requires_at_least_one_step_and_one_body_part():
    base = dict(id="x", name_zh="x", name_en="x", intensity="gentle", duration="1 分鐘")
    with pytest.raises(ValidationError):
        Pose(**base, body_parts=["neck"], steps=[])
    with pytest.raises(ValidationError):
        Pose(**base, body_parts=[], steps=["站好"])
    pose = Pose(**base, body_parts=["neck"], steps=["站好"])
    assert pose.cautions == [] and pose.contraindications == [] and pose.image is None


def test_pose_rejects_unknown_intensity():
    with pytest.raises(ValidationError):
        Pose(id="x", name_zh="x", name_en="x", body_parts=["neck"], intensity="hard",
             duration="1", steps=["a"])


def test_body_part_requires_a_view():
    with pytest.raises(ValidationError):
        BodyPart(id="neck", name_zh="頸部", views=[])


def test_advice_request_is_an_answers():
    req = AdviceRequest(body_part="neck", severity="mild", duration="today", cause="unknown")
    assert isinstance(req, Answers)
    assert req.severity is Severity.MILD
