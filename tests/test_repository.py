import pytest

from tests.conftest import make_pose
from yoga_relief.models import BodyPart
from yoga_relief.repository import DataError, Repository


def test_load_from_yaml_dir(sample_data_dir):
    repo = Repository.load(sample_data_dir)
    assert [p.id for p in repo.body_parts] == ["neck", "knee"]
    assert repo.get_body_part("knee").name_zh == "膝蓋"
    assert repo.get_body_part("nope") is None


def test_poses_for_keeps_file_order_and_filters_gentle(sample_parts, sample_poses):
    repo = Repository(sample_parts, sample_poses)
    assert [p.id for p in repo.poses_for("neck")] == ["a", "b", "c"]
    assert [p.id for p in repo.poses_for("knee", gentle_only=True)] == ["b", "d"]
    assert repo.poses_for("nope") == []


def test_duplicate_body_part_id_rejected(sample_poses):
    parts = [BodyPart(id="neck", name_zh="a", views=["front"]),
             BodyPart(id="neck", name_zh="b", views=["front"])]
    with pytest.raises(DataError, match="body_parts.*neck"):
        Repository(parts, sample_poses)


def test_duplicate_pose_id_rejected(sample_parts, sample_poses):
    with pytest.raises(DataError, match="poses.*a"):
        Repository(sample_parts, sample_poses + [make_pose("a", ["neck"])])


def test_pose_referencing_unknown_part_rejected(sample_parts, sample_poses):
    with pytest.raises(DataError, match="ghost"):
        Repository(sample_parts, sample_poses + [make_pose("z", ["ghost"])])


def test_part_needs_three_poses(sample_parts, sample_poses):
    # knee 只剩 b, c
    with pytest.raises(DataError, match="knee.*3"):
        Repository(sample_parts, [p for p in sample_poses if p.id != "d"])


def test_part_needs_two_gentle_poses(sample_parts, sample_poses):
    # knee: b(gentle) c(moderate) d→改成 moderate ⇒ 只剩 1 個 gentle
    poses = [p if p.id != "d" else make_pose("d", ["knee"], "moderate") for p in sample_poses]
    with pytest.raises(DataError, match="knee.*gentle"):
        Repository(sample_parts, poses)


def test_invalid_yaml_entry_reports_file(sample_data_dir):
    (sample_data_dir / "poses.yaml").write_text("- id: broken\n", encoding="utf-8")
    with pytest.raises(DataError, match="poses.yaml"):
        Repository.load(sample_data_dir)
