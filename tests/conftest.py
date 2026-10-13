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


class _FakeResponse:
    def __init__(self, parsed_output, stop_reason="end_turn"):
        self.parsed_output = parsed_output
        self.stop_reason = stop_reason


class _FakeMessages:
    def __init__(self, outputs: list):
        self._outputs = list(outputs)
        self.calls: list[dict] = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if not self._outputs:
            raise AssertionError("FakeClient：沒有預先放好的回應了")
        item = self._outputs.pop(0)
        if isinstance(item, Exception):
            raise item
        if item is None:
            return _FakeResponse(None, stop_reason="refusal")
        return _FakeResponse(item)


class FakeClient:
    """模仿 anthropic.Anthropic() 的最小介面：只有 messages.parse。"""

    def __init__(self, outputs: list):
        self.messages = _FakeMessages(outputs)
