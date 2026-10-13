"""呼叫 Claude 產生一組「部位 + 答案 + 動作清單」的個人化說明，並驗證回應形狀。

這個模組不決定何時呼叫（那是 build_advice 與 LiveAdvisor 的事），只負責「怎麼呼叫」。
"""

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
- why 的每一句不超過 40 字，說這個動作對他這個狀況的幫助。
- order 是建議的練習順序，必須剛好包含清單裡每個動作的 id 各一次。
- 語氣溫和，不用驚嘆號。"""


class AdviceValidationError(ValueError):
    """Claude 的回應沒有通過形狀檢查。"""


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
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_prompt(body_part, answers, poses)}],
        output_format=AdviceOutput,
        output_config={"effort": "low"},
    )
    output = response.parsed_output
    if output is None:
        raise AdviceValidationError(
            f"沒有 parsed_output（stop_reason={getattr(response, 'stop_reason', None)!r}）"
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
