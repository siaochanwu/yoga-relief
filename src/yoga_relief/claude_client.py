"""呼叫 Claude 產生一組「部位 + 答案 + 動作清單」的個人化說明，並驗證回應形狀。

這個模組不決定何時呼叫（那是 build_advice 與 LiveAdvisor 的事），只負責「怎麼呼叫」。
"""

from pydantic import BaseModel

from yoga_relief.config import Settings
from yoga_relief.models import (
    CAUSE_LABELS,
    DURATION_LABELS,
    SEVERITY_LABELS,
    AdviceOutput,
    Answers,
    BodyPart,
    Pose,
)

SYSTEM_PROMPT = """你是一位溫和、專業的瑜伽老師，用繁體中文說話。

使用者會告訴你：酸痛部位、疼痛程度、持續多久、可能原因，以及系統已經挑好的動作清單。
你的工作是依使用者的狀況，說明這些動作為什麼適合他，並建議練習順序。

規則：
- 只能針對清單裡的動作說明，不得新增、改名或刪除動作。
- 不得診斷病名，不得建議用藥或療程。
- summary 寫 2 到 3 句，先同理狀況，再說明整體練習方向。
- why 是一個陣列，清單裡每個動作各一筆：pose_id 填動作的 id。
- 每筆 why 不超過 40 字，說這個動作對他這個狀況的幫助。
- order 是建議的練習順序，必須剛好包含清單裡每個動作的 id 各一次。
- 語氣溫和，不用驚嘆號。"""


class WhyItem(BaseModel):
    pose_id: str
    why: str


class ClaudeAdvice(BaseModel):
    """送給 Claude 的 structured output 形狀（wire model）。

    不能用 dict[str, str]：Anthropic 的 structured output 不支援 additionalProperties，
    SDK 會把它改寫成空物件，模型就只能回 {}。所以 why 用「明確欄位的陣列」。
    """

    summary: str
    why: list[WhyItem]
    order: list[str]


class AdviceValidationError(ValueError):
    """Claude 的回應沒有通過形狀檢查。"""


def make_anthropic_client(settings: Settings):
    """用 Settings 裡的 key 建 SDK client；key 為 None 時 SDK 會自己找環境變數或登入檔。"""
    import anthropic

    return anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=30.0)


def build_user_prompt(body_part: BodyPart, answers: Answers, poses: list[Pose]) -> str:
    lines = [
        f"酸痛部位：{body_part.name_zh}",
        f"疼痛程度：{SEVERITY_LABELS[answers.severity]}",
        f"持續多久：{DURATION_LABELS[answers.duration]}",
        f"可能原因：{CAUSE_LABELS[answers.cause]}",
        "",
        "動作清單：",
    ]
    for pose in poses:
        lines.append(
            f"- id: {pose.id}；名稱：{pose.name_zh}（{pose.name_en}）；強度：{pose.intensity}"
        )
        lines.append(f"  步驟：{' '.join(pose.steps)}")
    return "\n".join(lines)


def generate_advice(
    client,
    *,
    model: str,
    body_part: BodyPart,
    answers: Answers,
    poses: list[Pose],
) -> AdviceOutput:
    response = client.messages.parse(
        model=model,
        max_tokens=4096,  # opus 的 adaptive thinking 也算在這個額度裡
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(body_part, answers, poses)}],
        output_format=ClaudeAdvice,
        output_config={"effort": "low"},
    )
    wire: ClaudeAdvice | None = response.parsed_output
    if wire is None:
        raise AdviceValidationError(
            f"沒有 parsed_output（stop_reason={getattr(response, 'stop_reason', None)!r}）"
        )
    output = AdviceOutput(
        summary=wire.summary,
        why={item.pose_id: item.why for item in wire.why},
        order=wire.order,
    )
    _validate(output, [p.id for p in poses])
    return output


def _validate(output: AdviceOutput, pose_ids: list[str]) -> None:
    expected = set(pose_ids)
    if not output.summary.strip():
        raise AdviceValidationError("summary 是空的")
    if set(output.why) != expected:
        raise AdviceValidationError(
            f"why 的 key {sorted(output.why)} 與動作 {sorted(expected)} 不符"
        )
    if len(output.order) != len(pose_ids) or set(output.order) != expected:
        raise AdviceValidationError(f"order {output.order} 不是動作 {sorted(expected)} 的排列")
