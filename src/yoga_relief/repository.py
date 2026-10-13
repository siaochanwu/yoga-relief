"""載入並驗證 body_parts.yaml 與 poses.yaml，提供依部位查動作。"""

from collections import Counter
from pathlib import Path

import yaml
from pydantic import TypeAdapter, ValidationError

from yoga_relief.models import BodyPart, Intensity, Pose

DATA_DIR = Path(__file__).parent / "data"

MIN_POSES_PER_PART = 3
MIN_GENTLE_PER_PART = 2


class DataError(ValueError):
    """資料檔內容不符合規則。訊息要說清楚是哪個檔、哪一筆、違反哪條。"""


class Repository:
    def __init__(self, body_parts: list[BodyPart], poses: list[Pose]) -> None:
        self._parts = list(body_parts)
        self._poses = list(poses)
        self._by_id = {p.id: p for p in self._parts}
        self._validate()

    @classmethod
    def load(cls, data_dir: Path = DATA_DIR) -> "Repository":
        parts = _load_yaml(data_dir / "body_parts.yaml", BodyPart)
        poses = _load_yaml(data_dir / "poses.yaml", Pose)
        return cls(parts, poses)

    @property
    def body_parts(self) -> list[BodyPart]:
        return list(self._parts)

    def get_body_part(self, body_part_id: str) -> BodyPart | None:
        return self._by_id.get(body_part_id)

    def poses_for(self, body_part_id: str, *, gentle_only: bool = False) -> list[Pose]:
        return [
            p
            for p in self._poses
            if body_part_id in p.body_parts
            and (not gentle_only or p.intensity is Intensity.GENTLE)
        ]

    def _validate(self) -> None:
        dup_parts = [k for k, n in Counter(p.id for p in self._parts).items() if n > 1]
        if dup_parts:
            raise DataError(f"body_parts.yaml 有重複 id：{dup_parts}")
        dup_poses = [k for k, n in Counter(p.id for p in self._poses).items() if n > 1]
        if dup_poses:
            raise DataError(f"poses.yaml 有重複 id：{dup_poses}")
        for pose in self._poses:
            unknown = [b for b in pose.body_parts if b not in self._by_id]
            if unknown:
                raise DataError(f"poses.yaml 的 {pose.id} 引用不存在的部位：{unknown}")
        for part in self._parts:
            total = len(self.poses_for(part.id))
            if total < MIN_POSES_PER_PART:
                raise DataError(
                    f"部位 {part.id} 只有 {total} 個動作，至少要 {MIN_POSES_PER_PART} 個"
                )
            gentle = len(self.poses_for(part.id, gentle_only=True))
            if gentle < MIN_GENTLE_PER_PART:
                raise DataError(
                    f"部位 {part.id} 只有 {gentle} 個 gentle 動作，至少要 {MIN_GENTLE_PER_PART} 個"
                )


def _load_yaml[T](path: Path, model: type[T]) -> list[T]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise DataError(f"找不到 {path.name}") from e
    try:
        return TypeAdapter(list[model]).validate_python(raw)
    except ValidationError as e:
        raise DataError(f"{path.name} 格式錯誤：\n{e}") from e
