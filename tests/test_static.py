import re

from yoga_relief.main import STATIC_DIR
from yoga_relief.repository import DATA_DIR, Repository


def test_svg_has_a_region_for_every_part_in_every_declared_view():
    svg = (STATIC_DIR / "body.svg").read_text(encoding="utf-8")
    repo = Repository.load(DATA_DIR)
    for view in ("front", "back"):
        group = re.search(rf'<g id="view-{view}"[^>]*>(.*?)</g>', svg, re.S).group(1)
        parts_in_view = set(re.findall(r'data-part="([a-z_]+)"', group))
        expected = {p.id for p in repo.body_parts if view in p.views}
        assert parts_in_view == expected, view


def test_index_references_all_assets():
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert '/static/style.css' in html and '/static/app.js' in html
    for screen in ("screen-select", "screen-questions", "screen-result", "screen-history"):
        assert f'id="{screen}"' in html


def test_every_pose_has_an_existing_svg_image():
    import xml.etree.ElementTree as ET

    repo = Repository.load(DATA_DIR)
    seen = set()
    for part in repo.body_parts:
        for pose in repo.poses_for(part.id):
            if pose.id in seen:
                continue
            seen.add(pose.id)
            assert pose.image == f"/static/images/{pose.id}.svg", pose.id
            path = STATIC_DIR / "images" / f"{pose.id}.svg"
            assert path.exists(), pose.id
            root = ET.fromstring(path.read_text(encoding="utf-8"))
            assert root.tag.endswith("svg"), pose.id
    assert len(seen) == 30
