"""所有測試共用的 fixture。"""

from pathlib import Path

import pytest
import yaml

from yoga_relief.models import BodyPart, Pose


def make_pose(id: str, parts: list[str], intensity: str = "gentle") -> Pose:
    return Pose(id=id, name_zh=id, name_en=id, body_parts=parts, intensity=intensity,
                duration="5 次呼吸", steps=["步驟一"])


@pytest.fixture
def sample_parts() -> list[BodyPart]:
    return [
        BodyPart(id="neck", name_zh="頸部", views=["front", "back"]),
        BodyPart(id="knee", name_zh="膝蓋", views=["front"]),
    ]


@pytest.fixture
def sample_poses() -> list[Pose]:
    return [
        make_pose("a", ["neck"]),
        make_pose("b", ["neck", "knee"]),
        make_pose("c", ["neck", "knee"], "moderate"),
        make_pose("d", ["knee"]),
    ]


@pytest.fixture
def sample_data_dir(tmp_path: Path, sample_parts, sample_poses) -> Path:
    (tmp_path / "body_parts.yaml").write_text(
        yaml.safe_dump([p.model_dump(mode="json") for p in sample_parts], allow_unicode=True),
        encoding="utf-8",
    )
    (tmp_path / "poses.yaml").write_text(
        yaml.safe_dump([p.model_dump(mode="json") for p in sample_poses], allow_unicode=True),
        encoding="utf-8",
    )
    return tmp_path
