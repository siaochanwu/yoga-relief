"""離線走訪所有「部位 × 三題答案」組合，呼叫 Claude 產生說明，寫入 advice.json。"""

import argparse
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import product
from pathlib import Path

from yoga_relief.advisor import DEFAULT_ADVICE_PATH, AdviceStore, advice_key
from yoga_relief.claude_client import generate_advice, make_anthropic_client
from yoga_relief.models import AdviceRecord, Answers, BodyPart, Cause, Duration, Severity
from yoga_relief.repository import DATA_DIR, Repository
from yoga_relief.triage import should_seek_medical


@dataclass
class Summary:
    generated: int = 0
    skipped: int = 0
    failed: list[str] = field(default_factory=list)


def combinations(repo: Repository) -> list[tuple[BodyPart, Answers]]:
    result = []
    for part in repo.body_parts:
        for severity, duration, cause in product(Severity, Duration, Cause):
            answers = Answers(severity=severity, duration=duration, cause=cause)
            if not should_seek_medical(answers):
                result.append((part, answers))
    return result


def run(
    repo: Repository,
    store: AdviceStore,
    client,
    *,
    model: str,
    out_path: Path,
    force: bool = False,
    log: Callable[[str], None] = print,
) -> Summary:
    summary = Summary()
    combos = combinations(repo)
    for index, (part, answers) in enumerate(combos, start=1):
        poses = repo.poses_for(part.id)
        pose_ids = [p.id for p in poses]
        key = advice_key(part.id, answers)
        if not force and store.lookup(key, pose_ids) is not None:
            summary.skipped += 1
            continue
        try:
            output = generate_advice(
                client, model=model, body_part=part, answers=answers, poses=poses
            )
        except Exception as e:  # noqa: BLE001 - 腳本要撐到最後，失敗的組合下次再補
            summary.failed.append(key)
            log(f"[{index}/{len(combos)}] 失敗 {key}：{e}")
            continue
        store.put(
            key,
            AdviceRecord(
                **output.model_dump(),
                pose_ids=pose_ids,
                model=model,
                generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
            ),
        )
        store.save(out_path)
        summary.generated += 1
        log(f"[{index}/{len(combos)}] 完成 {key}")
    return summary


def main(argv: list[str] | None = None) -> int:
    from yoga_relief.config import Settings

    parser = argparse.ArgumentParser(description="產生 advice.json")
    parser.add_argument("--force", action="store_true", help="忽略既有內容，全部重產")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    settings = Settings()
    repo = Repository.load(DATA_DIR)
    store = AdviceStore.load(DEFAULT_ADVICE_PATH)
    client = make_anthropic_client(settings)

    summary = run(
        repo, store, client, model=settings.claude_model, out_path=DEFAULT_ADVICE_PATH,
        force=args.force,
    )
    print(
        f"新產生 {summary.generated} 筆、跳過 {summary.skipped} 筆、"
        f"失敗 {len(summary.failed)} 筆"
    )
    for key in summary.failed:
        print(f"  失敗：{key}")
    return 1 if summary.failed else 0
