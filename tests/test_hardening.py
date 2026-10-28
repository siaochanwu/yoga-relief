"""公開部署前的加固：關掉 API 文件頁、每個回應都帶安全標頭。"""

import pytest
from fastapi.testclient import TestClient

from yoga_relief.config import Settings
from yoga_relief.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(advice_path=tmp_path / "none.json", settings=Settings(_env_file=None))
    return TestClient(app)


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_api_docs_pages_are_disabled(client, path):
    assert client.get(path).status_code == 404


@pytest.mark.parametrize("path", ["/", "/api/body-parts", "/static/app.js", "/no-such-page"])
def test_every_response_has_security_headers(client, path):
    res = client.get(path)
    assert res.headers["x-content-type-options"] == "nosniff"
    assert res.headers["referrer-policy"] == "no-referrer"
    assert res.headers["x-frame-options"] == "DENY"
    csp = res.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
