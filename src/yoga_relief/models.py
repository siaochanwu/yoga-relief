"""所有資料形狀的單一來源：枚舉、YAML 資料、API 請求／回應、advice.json 記錄。"""

from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class Duration(StrEnum):
    TODAY = "today"
    DAYS = "days"
    WEEK_PLUS = "week_plus"
    MONTH_PLUS = "month_plus"


class Cause(StrEnum):
    SEDENTARY = "sedentary"
    EXERTION = "exertion"
    SLEEP = "sleep"
    INJURY = "injury"
    UNKNOWN = "unknown"


class Intensity(StrEnum):
    GENTLE = "gentle"
    MODERATE = "moderate"


class View(StrEnum):
    FRONT = "front"
    BACK = "back"


SEVERITY_LABELS: dict[Severity, str] = {
    Severity.MILD: "輕微",
    Severity.MODERATE: "中等",
    Severity.SEVERE: "嚴重",
}
DURATION_LABELS: dict[Duration, str] = {
    Duration.TODAY: "今天才開始",
    Duration.DAYS: "幾天",
    Duration.WEEK_PLUS: "一週以上",
    Duration.MONTH_PLUS: "一個月以上",
}
CAUSE_LABELS: dict[Cause, str] = {
    Cause.SEDENTARY: "久坐久站",
    Cause.EXERTION: "運動或勞動後",
    Cause.SLEEP: "睡姿或落枕",
    Cause.INJURY: "受傷或跌倒",
    Cause.UNKNOWN: "不確定",
}


# ---- YAML 資料 ----


class BodyPart(BaseModel):
    id: str
    name_zh: str
    views: list[View] = Field(min_length=1)


class Pose(BaseModel):
    id: str
    name_zh: str
    name_en: str
    body_parts: list[str] = Field(min_length=1)
    intensity: Intensity
    duration: str
    steps: list[str] = Field(min_length=1)
    cautions: list[str] = []
    contraindications: list[str] = []
    image: str | None = None


# ---- 問卷與 API ----


class Answers(BaseModel):
    severity: Severity
    duration: Duration
    cause: Cause


class AdviceRequest(Answers):
    body_part: str


class BodyPartRef(BaseModel):
    id: str
    name_zh: str


class PoseWithWhy(Pose):
    why: str | None = None


class AdviceSummary(BaseModel):
    summary: str


class AdviceResponse(BaseModel):
    body_part: BodyPartRef
    seek_medical: bool
    poses: list[PoseWithWhy]
    advice: AdviceSummary | None


# ---- AI 說明 ----


class AdviceOutput(BaseModel):
    """Claude structured output 的形狀。"""

    summary: str
    why: dict[str, str]
    order: list[str]


class AdviceRecord(AdviceOutput):
    """advice.json 裡的一筆。"""

    pose_ids: list[str]
    model: str
    generated_at: str
