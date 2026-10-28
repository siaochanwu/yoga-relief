"""離線預產的 AI 說明資料庫（advice.json）的讀寫與查詢。"""

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from pydantic import TypeAdapter

from yoga_relief.claude_client import generate_advice
from yoga_relief.models import AdviceRecord, Answers, BodyPart, Pose

log = logging.getLogger(__name__)

DEFAULT_ADVICE_PATH = Path(__file__).parent / "data" / "advice.json"

_RECORDS = TypeAdapter(dict[str, AdviceRecord])


def advice_key(body_part_id: str, answers: Answers) -> str:
    return f"{body_part_id}|{answers.severity}|{answers.duration}|{answers.cause}"


class AdviceStore:
    def __init__(self, records: dict[str, AdviceRecord] | None = None) -> None:
        self._records: dict[str, AdviceRecord] = dict(records or {})

    @classmethod
    def load(cls, path: Path = DEFAULT_ADVICE_PATH) -> "AdviceStore":
        if not path.exists():
            log.warning("找不到 %s，所有查詢的 advice 都會是 null", path.name)
            return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(_RECORDS.validate_python(raw))

    def lookup(self, key: str, current_pose_ids: list[str]) -> AdviceRecord | None:
        record = self._records.get(key)
        if record is None or set(record.pose_ids) != set(current_pose_ids):
            return None
        return record

    def put(self, key: str, record: AdviceRecord) -> None:
        self._records[key] = record

    def save(self, path: Path) -> None:
        payload = {k: self._records[k].model_dump(mode="json") for k in sorted(self._records)}
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, path)

    def __len__(self) -> int:
        return len(self._records)

    def __contains__(self, key: object) -> bool:
        return key in self._records


class LiveAdvisor:
    """開發用：查不到 advice.json 時即時呼叫 Claude。結果只存記憶體。"""

    def __init__(self, client, model: str) -> None:
        self._client = client
        self._model = model
        self._cache: dict[str, AdviceRecord] = {}

    def get(
        self, key: str, body_part: BodyPart, answers: Answers, poses: list[Pose]
    ) -> AdviceRecord | None:
        if key in self._cache:
            return self._cache[key]
        try:
            output = generate_advice(
                self._client, model=self._model, body_part=body_part, answers=answers, poses=poses
            )
        except Exception:  # noqa: BLE001 - 即時模式失敗只影響 advice 欄位，不能讓 API 500
            log.exception("即時呼叫 Claude 失敗（key=%s）", key)
            return None
        record = AdviceRecord(
            **output.model_dump(),
            pose_ids=[p.id for p in poses],
            model=self._model,
            generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        self._cache[key] = record
        return record
