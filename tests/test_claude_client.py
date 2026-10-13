import pytest

from tests.conftest import FakeClient, make_pose
from yoga_relief.claude_client import (
    SYSTEM_PROMPT,
    AdviceValidationError,
    build_user_prompt,
    generate_advice,
)
from yoga_relief.models import AdviceOutput, Answers, BodyPart

PART = BodyPart(id="neck", name_zh="頸部", views=["front"])
ANSWERS = Answers(severity="mild", duration="days", cause="sedentary")
POSES = [make_pose("a", ["neck"]), make_pose("b", ["neck"])]


def good_output() -> AdviceOutput:
    return AdviceOutput(summary="總結。", why={"a": "因 a", "b": "因 b"}, order=["b", "a"])


def test_prompt_contains_labels_and_pose_ids():
    text = build_user_prompt(PART, ANSWERS, POSES)
    assert "頸部" in text and "輕微" in text and "幾天" in text and "久坐久站" in text
    assert "id: a" in text and "id: b" in text


def test_generate_advice_calls_parse_with_expected_params():
    client = FakeClient([good_output()])
    out = generate_advice(client, model="m", body_part=PART, answers=ANSWERS, poses=POSES)
    assert out.order == ["b", "a"]
    call = client.messages.calls[0]
    assert call["model"] == "m"
    assert call["system"] == SYSTEM_PROMPT
    assert call["output_format"] is AdviceOutput
    assert call["output_config"] == {"effort": "low"}
    assert call["messages"][0]["role"] == "user"


def test_refusal_or_missing_parsed_output_raises():
    client = FakeClient([None])
    with pytest.raises(AdviceValidationError, match="refusal"):
        generate_advice(client, model="m", body_part=PART, answers=ANSWERS, poses=POSES)


@pytest.mark.parametrize(
    "bad",
    [
        AdviceOutput(summary="x", why={"a": "1"}, order=["a", "b"]),          # why 少 b
        AdviceOutput(summary="x", why={"a": "1", "b": "2", "c": "3"}, order=["a", "b"]),  # why 多 c
        AdviceOutput(summary="x", why={"a": "1", "b": "2"}, order=["a"]),     # order 少
        AdviceOutput(summary="x", why={"a": "1", "b": "2"}, order=["a", "a"]),  # order 重複
        AdviceOutput(summary="x", why={"a": "1", "b": "2"}, order=["a", "zz"]),  # order 未知
        AdviceOutput(summary="   ", why={"a": "1", "b": "2"}, order=["a", "b"]),  # 空 summary
    ],
)
def test_invalid_output_shapes_raise(bad):
    client = FakeClient([bad])
    with pytest.raises(AdviceValidationError):
        generate_advice(client, model="m", body_part=PART, answers=ANSWERS, poses=POSES)
