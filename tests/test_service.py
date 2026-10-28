import pytest

from tests.conftest import FakeClient
from yoga_relief.advisor import AdviceStore, LiveAdvisor, advice_key
from yoga_relief.models import AdviceOutput, AdviceRecord, AdviceRequest
from yoga_relief.repository import Repository
from yoga_relief.service import AdviceService, UnknownBodyPart


@pytest.fixture
def repo(sample_parts, sample_poses):
    return Repository(sample_parts, sample_poses)


def req(**over) -> AdviceRequest:
    base = dict(body_part="neck", severity="mild", duration="days", cause="sedentary")
    return AdviceRequest(**(base | over))


def record(order, why, pose_ids=("a", "b", "c")) -> AdviceRecord:
    return AdviceRecord(summary="總結", why=why, order=order, pose_ids=list(pose_ids),
                        model="m", generated_at="t")


def test_unknown_part_raises(repo):
    with pytest.raises(UnknownBodyPart):
        AdviceService(repo, AdviceStore()).advise(req(body_part="ghost"))


def test_no_advice_keeps_file_order_and_null_fields(repo):
    res = AdviceService(repo, AdviceStore()).advise(req())
    assert res.body_part.id == "neck" and res.body_part.name_zh == "頸部"
    assert res.seek_medical is False
    assert [p.id for p in res.poses] == ["a", "b", "c"]
    assert all(p.why is None for p in res.poses)
    assert res.advice is None


def test_advice_hit_orders_and_fills_why(repo):
    store = AdviceStore({advice_key("neck", req()): record(
        order=["c", "a", "b"], why={"a": "A", "b": "B", "c": "C"})})
    res = AdviceService(repo, store).advise(req())
    assert [p.id for p in res.poses] == ["c", "a", "b"]
    assert [p.why for p in res.poses] == ["C", "A", "B"]
    assert res.advice.summary == "總結"


def test_hand_edited_record_with_missing_why_and_unknown_order_is_tolerated(repo):
    # Review Focus 1：why 少 b、order 含不存在的 zz、order 漏 a
    store = AdviceStore({advice_key("neck", req()): record(
        order=["zz", "c", "b"], why={"a": "A", "c": "C"})})
    res = AdviceService(repo, store).advise(req())
    assert [p.id for p in res.poses] == ["c", "b", "a"]      # 已知的照 order，漏的補最後
    assert [p.why for p in res.poses] == ["C", None, "A"]


def test_seek_medical_only_gentle_and_no_advice_even_if_record_exists(repo):
    r = req(severity="severe", duration="month_plus")
    store = AdviceStore({advice_key("neck", r): record(
        order=["a", "b", "c"], why={"a": "A", "b": "B", "c": "C"})})
    res = AdviceService(repo, store).advise(r)
    assert res.seek_medical is True
    assert [p.id for p in res.poses] == ["a", "b"]           # c 是 moderate
    assert res.advice is None and all(p.why is None for p in res.poses)


def test_live_advisor_used_only_on_miss(repo):
    good = AdviceOutput(summary="live", why={"a": "1", "b": "2", "c": "3"}, order=["a", "b", "c"])
    client = FakeClient([good])
    service = AdviceService(repo, AdviceStore(), live=LiveAdvisor(client, "m"))
    assert service.advise(req()).advice.summary == "live"
    assert service.advise(req()).advice.summary == "live"
    assert len(client.messages.calls) == 1


def test_duplicate_ids_in_order_render_each_pose_once(repo):
    store = AdviceStore({advice_key("neck", req()): record(
        order=["c", "c", "a", "b"], why={"a": "A", "b": "B", "c": "C"})})
    res = AdviceService(repo, store).advise(req())
    assert [p.id for p in res.poses] == ["c", "a", "b"]
