"""把 repository、triage、advisor 組成一次「建議」的流程。沒有 HTTP 概念，可直接測。"""

from yoga_relief.advisor import AdviceStore, LiveAdvisor, advice_key
from yoga_relief.models import (
    AdviceRecord,
    AdviceRequest,
    AdviceResponse,
    AdviceSummary,
    BodyPartRef,
    Pose,
    PoseWithWhy,
)
from yoga_relief.repository import Repository
from yoga_relief.triage import should_seek_medical


class UnknownBodyPart(KeyError):
    pass


class AdviceService:
    def __init__(
        self, repo: Repository, store: AdviceStore, live: LiveAdvisor | None = None
    ) -> None:
        self._repo = repo
        self._store = store
        self._live = live

    def advise(self, req: AdviceRequest) -> AdviceResponse:
        part = self._repo.get_body_part(req.body_part)
        if part is None:
            raise UnknownBodyPart(req.body_part)

        seek = should_seek_medical(req)
        poses = self._repo.poses_for(part.id, gentle_only=seek)

        record: AdviceRecord | None = None
        if not seek:
            key = advice_key(part.id, req)
            record = self._store.lookup(key, [p.id for p in poses])
            if record is None and self._live is not None:
                record = self._live.get(key, part, req, poses)

        ordered = _apply_order(poses, record)
        return AdviceResponse(
            body_part=BodyPartRef(id=part.id, name_zh=part.name_zh),
            seek_medical=seek,
            poses=[
                PoseWithWhy(**p.model_dump(), why=record.why.get(p.id) if record else None)
                for p in ordered
            ],
            advice=AdviceSummary(summary=record.summary) if record else None,
        )


def _apply_order(poses: list[Pose], record: AdviceRecord | None) -> list[Pose]:
    """依 record.order 排序；未知 id 忽略、漏掉的動作補在最後。沒有 record 就維持原順序。"""
    if record is None:
        return poses
    by_id = {p.id: p for p in poses}
    ordered: list[Pose] = []
    seen: set[str] = set()
    for pose_id in record.order:
        if pose_id in by_id and pose_id not in seen:
            ordered.append(by_id[pose_id])
            seen.add(pose_id)
    ordered.extend(p for p in poses if p.id not in seen)
    return ordered
