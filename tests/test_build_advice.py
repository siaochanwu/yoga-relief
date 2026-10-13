from tests.conftest import FakeClient
from yoga_relief.advisor import AdviceStore, advice_key
from yoga_relief.build_advice import Summary, combinations, run
from yoga_relief.claude_client import AdviceValidationError
from yoga_relief.models import AdviceOutput, AdviceRecord
from yoga_relief.repository import DATA_DIR, Repository
from yoga_relief.triage import should_seek_medical


def test_combinations_exclude_seek_medical_cases():
    repo = Repository.load(DATA_DIR)
    combos = combinations(repo)
    assert len(combos) == 576                       # 720 - 144
    assert not any(should_seek_medical(a) for _, a in combos)
    assert len({(p.id, advice_key(p.id, a)) for p, a in combos}) == 576


def _good(repo: Repository, part_id: str) -> AdviceOutput:
    ids = [p.id for p in repo.poses_for(part_id)]
    return AdviceOutput(summary="s", why={i: "w" for i in ids}, order=ids)


def test_run_generates_everything_and_saves_incrementally(sample_parts, sample_poses, tmp_path):
    repo = Repository(sample_parts, sample_poses)
    combos = combinations(repo)
    client = FakeClient([_good(repo, p.id) for p, _ in combos])
    store = AdviceStore()
    out = tmp_path / "advice.json"

    summary = run(repo, store, client, model="m", out_path=out, log=lambda *_: None)

    assert summary == Summary(generated=len(combos), skipped=0, failed=[])
    assert len(AdviceStore.load(out)) == len(combos)
    assert len(client.messages.calls) == len(combos)


def test_run_skips_existing_and_regenerates_stale(sample_parts, sample_poses, tmp_path):
    repo = Repository(sample_parts, sample_poses)
    combos = combinations(repo)
    first_part, first_answers = combos[0]
    key = advice_key(first_part.id, first_answers)
    ids = [p.id for p in repo.poses_for(first_part.id)]
    fresh = AdviceRecord(summary="s", why={i: "w" for i in ids}, order=ids,
                         pose_ids=ids, model="old", generated_at="t")
    stale = fresh.model_copy(update={"pose_ids": ["ghost"]})
    second_part, second_answers = combos[1]
    store = AdviceStore({key: fresh, advice_key(second_part.id, second_answers): stale})

    client = FakeClient([_good(repo, p.id) for p, _ in combos[1:]])
    summary = run(repo, store, client, model="m", out_path=tmp_path / "a.json",
                  log=lambda *_: None)

    assert summary.skipped == 1
    assert summary.generated == len(combos) - 1
    assert len(client.messages.calls) == len(combos) - 1


def test_run_force_regenerates_all(sample_parts, sample_poses, tmp_path):
    repo = Repository(sample_parts, sample_poses)
    combos = combinations(repo)
    ids = [p.id for p in repo.poses_for(combos[0][0].id)]
    store = AdviceStore({advice_key(combos[0][0].id, combos[0][1]): AdviceRecord(
        summary="s", why={i: "w" for i in ids}, order=ids, pose_ids=ids, model="old",
        generated_at="t")})
    client = FakeClient([_good(repo, p.id) for p, _ in combos])

    summary = run(repo, store, client, model="m", out_path=tmp_path / "a.json", force=True,
                  log=lambda *_: None)

    assert summary.skipped == 0 and summary.generated == len(combos)


def test_run_records_failures_and_continues(sample_parts, sample_poses, tmp_path):
    repo = Repository(sample_parts, sample_poses)
    combos = combinations(repo)
    outputs = [_good(repo, p.id) for p, _ in combos]
    outputs[0] = AdviceValidationError("bad shape")
    outputs[1] = RuntimeError("network down")
    client = FakeClient(outputs)
    store = AdviceStore()
    logs: list[str] = []

    summary = run(repo, store, client, model="m", out_path=tmp_path / "a.json",
                  log=lambda msg: logs.append(msg))

    assert summary.generated == len(combos) - 2
    assert summary.failed == [advice_key(p.id, a) for p, a in combos[:2]]
    assert any("bad shape" in m for m in logs) and any("network down" in m for m in logs)
