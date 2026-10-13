from yoga_relief.repository import DATA_DIR, Repository

EXPECTED_PARTS = [
    "neck", "shoulder", "chest", "wrist", "hip", "thigh", "knee", "ankle",
    "upper_back", "lower_back", "glute", "calf",
]


def test_real_data_loads_and_has_twelve_parts():
    repo = Repository.load(DATA_DIR)
    assert [p.id for p in repo.body_parts] == EXPECTED_PARTS


def test_every_part_has_three_to_many_poses_and_two_gentle():
    # Repository 已強制；這裡再明確斷言一次，資料改壞時訊息更直接
    repo = Repository.load(DATA_DIR)
    for part in repo.body_parts:
        assert len(repo.poses_for(part.id)) >= 3, part.id
        assert len(repo.poses_for(part.id, gentle_only=True)) >= 2, part.id
