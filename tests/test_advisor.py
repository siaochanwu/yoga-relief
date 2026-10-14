import json

import pytest

from tests.conftest import FakeClient, make_pose
from yoga_relief.advisor import AdviceStore, LiveAdvisor, advice_key
from yoga_relief.models import AdviceOutput, AdviceRecord, Answers, BodyPart


def make_record(pose_ids=("a", "b")) -> AdviceRecord:
    return AdviceRecord(
        summary="總結", why={p: f"因為 {p}" for p in pose_ids}, order=list(pose_ids),
        pose_ids=list(pose_ids), model="test-model", generated_at="2026-10-08T00:00:00+08:00",
    )


def test_advice_key_format():
    answers = Answers(severity="mild", duration="today", cause="unknown")
    assert advice_key("neck", answers) == "neck|mild|today|unknown"


def test_lookup_hit_and_miss():
    store = AdviceStore({"k": make_record()})
    assert store.lookup("k", ["b", "a"]) is not None   # 順序不同仍算命中
    assert store.lookup("nope", ["a", "b"]) is None


def test_lookup_treats_changed_pose_set_as_stale():
    store = AdviceStore({"k": make_record(("a", "b"))})
    assert store.lookup("k", ["a", "b", "c"]) is None
    assert store.lookup("k", ["a"]) is None


def test_load_missing_file_gives_empty_store(tmp_path, caplog):
    store = AdviceStore.load(tmp_path / "advice.json")
    assert len(store) == 0
    assert "advice.json" in caplog.text


def test_load_invalid_json_raises(tmp_path):
    path = tmp_path / "advice.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        AdviceStore.load(path)


def test_load_invalid_record_raises(tmp_path):
    path = tmp_path / "advice.json"
    path.write_text(json.dumps({"k": {"summary": "x"}}), encoding="utf-8")
    with pytest.raises(ValueError):
        AdviceStore.load(path)


def test_put_save_load_roundtrip(tmp_path):
    path = tmp_path / "advice.json"
    store = AdviceStore()
    store.put("z", make_record())
    store.put("a", make_record())
    store.save(path)
    text = path.read_text(encoding="utf-8")
    assert text.index('"a"') < text.index('"z"')   # key 排序，diff 才穩定
    assert "總結" in text                            # 不是 \\uXXXX
    again = AdviceStore.load(path)
    assert "z" in again and again.lookup("z", ["a", "b"]).summary == "總結"


_PART = BodyPart(id="neck", name_zh="頸部", views=["front"])
_ANS = Answers(severity="mild", duration="days", cause="sleep")
_POSES = [make_pose("a", ["neck"]), make_pose("b", ["neck"])]


def test_live_advisor_caches_and_swallows_errors():
    good = AdviceOutput(summary="s", why={"a": "1", "b": "2"}, order=["a", "b"])
    client = FakeClient([RuntimeError("boom"), good])
    live = LiveAdvisor(client, "m")
    assert live.get("k", _PART, _ANS, _POSES) is None          # 第一次失敗
    rec = live.get("k", _PART, _ANS, _POSES)                    # 第二次成功
    assert rec is not None and rec.pose_ids == ["a", "b"]
    assert live.get("k", _PART, _ANS, _POSES) is rec            # 第三次用快取
    assert len(client.messages.calls) == 2
