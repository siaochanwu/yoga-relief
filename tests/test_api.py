import pytest
from fastapi.testclient import TestClient

from yoga_relief.advisor import advice_key
from yoga_relief.config import Settings
from yoga_relief.main import create_app
from yoga_relief.models import AdviceRecord, AdviceRequest


@pytest.fixture
def client(tmp_path):
    # 真的 YAML、空的 advice.json（指到不存在的路徑）、關閉即時模式
    app = create_app(advice_path=tmp_path / "none.json", settings=Settings(_env_file=None))
    return TestClient(app)


def test_body_parts(client):
    res = client.get("/api/body-parts")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 12
    assert data[0] == {"id": "neck", "name_zh": "頸部", "views": ["front", "back"]}


def test_advice_without_record(client):
    res = client.post("/api/advice", json={
        "body_part": "neck", "severity": "mild", "duration": "days", "cause": "sedentary"})
    assert res.status_code == 200
    body = res.json()
    assert body["seek_medical"] is False and body["advice"] is None
    assert len(body["poses"]) >= 3 and body["poses"][0]["why"] is None
    assert body["poses"][0]["image"].startswith("/static/images/")
    assert {"id", "name_zh", "name_en", "steps", "duration", "cautions",
            "contraindications", "intensity", "why"} <= set(body["poses"][0])


def test_advice_with_record(client):
    app = client.app
    repo, store = app.state.repo, app.state.store
    req = AdviceRequest(body_part="neck", severity="mild", duration="days", cause="sedentary")
    ids = [p.id for p in repo.poses_for("neck")]
    store.put(advice_key("neck", req), AdviceRecord(
        summary="總結", why={i: f"因 {i}" for i in ids}, order=list(reversed(ids)),
        pose_ids=ids, model="m", generated_at="t"))
    body = client.post("/api/advice", json=req.model_dump(mode="json")).json()
    assert body["advice"] == {"summary": "總結"}
    assert [p["id"] for p in body["poses"]] == list(reversed(ids))


def test_seek_medical_response(client):
    body = client.post("/api/advice", json={
        "body_part": "knee", "severity": "moderate", "duration": "today", "cause": "injury"}).json()
    assert body["seek_medical"] is True
    assert all(p["intensity"] == "gentle" for p in body["poses"])
    assert body["advice"] is None


@pytest.mark.parametrize("part", ["ghost", "Neck", "neck ", ""])
def test_unknown_or_unnormalised_part_is_404(client, part):
    res = client.post("/api/advice", json={
        "body_part": part, "severity": "mild", "duration": "days", "cause": "sedentary"})
    assert res.status_code == 404
    assert res.json()["detail"].startswith("unknown body part")


def test_bad_enum_and_missing_field_are_422(client):
    assert client.post("/api/advice", json={
        "body_part": "neck", "severity": "huge", "duration": "days", "cause": "sedentary"
    }).status_code == 422
    assert client.post("/api/advice", json={"body_part": "neck"}).status_code == 422


def test_index_and_static(client):
    res = client.get("/")
    assert res.status_code == 200 and "text/html" in res.headers["content-type"]
    assert 'id="app"' in res.text
