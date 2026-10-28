"""就醫分流規則。純函式，不碰 AI、不碰資料檔。"""

from yoga_relief.models import Answers, Cause, Duration, Severity

SEEK_MEDICAL_TEXT = (
    "你的狀況建議先由醫師或物理治療師評估。"
    "以下只列出最溫和的動作，若做了更痛請立即停止。"
)


def should_seek_medical(answers: Answers) -> bool:
    chronic_severe = (
        answers.severity is Severity.SEVERE and answers.duration is Duration.MONTH_PLUS
    )
    injury_not_mild = answers.cause is Cause.INJURY and answers.severity in (
        Severity.MODERATE,
        Severity.SEVERE,
    )
    return chronic_severe or injury_not_mild
