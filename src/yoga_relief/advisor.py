"""離線預產的 AI 說明資料庫（advice.json）的讀寫與查詢。"""

import json
import logging
import os
from pathlib import Path

from pydantic import TypeAdapter

from yoga_relief.models import AdviceRecord, Answers

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
