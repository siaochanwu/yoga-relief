import pytest

from tests.conftest import FakeClient, make_pose
from yoga_relief.claude_client import (
    SYSTEM_PROMPT,
    AdviceValidationError,
    ClaudeAdvice,
    build_user_prompt,
    generate_advice,
    make_anthropic_client,
)
from yoga_relief.config import Settings
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
    assert call["output_format"] is ClaudeAdvice
    assert call["output_config"] == {"effort": "low"}
    assert call["max_tokens"] >= 4096   # opus 的 thinking 也算在 max_tokens 裡，1024 會截斷
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


def test_wire_schema_survives_sdk_transform():
    # Anthropic structured output 不支援 additionalProperties 型別，SDK 會把 dict[str, str]
    # 改寫成空物件；wire model 必須用明確欄位，這個測試鎖住這件事。
    from anthropic.lib._parse._transform import transform_schema

    schema = transform_schema(ClaudeAdvice.model_json_schema())
    why = schema["properties"]["why"]
    assert why["type"] == "array"
    item = why["items"]
    if "$ref" in item:
        item = schema["$defs"][item["$ref"].rsplit("/", 1)[-1]]
    assert set(item["properties"]) == {"pose_id", "why"}
    assert set(item["required"]) == {"pose_id", "why"}


def test_make_anthropic_client_passes_key_and_timeout(monkeypatch):
    import anthropic

    captured = {}

    class FakeAnthropic:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(anthropic, "Anthropic", FakeAnthropic)
    settings = Settings(_env_file=None, ANTHROPIC_API_KEY="sk-test")
    make_anthropic_client(settings)
    assert captured["api_key"] == "sk-test"
    assert captured["timeout"] == 30.0
