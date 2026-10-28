"""建立 FastAPI app：載入資料、組裝 service、掛路由與靜態檔。"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from yoga_relief.advisor import DEFAULT_ADVICE_PATH, AdviceStore, LiveAdvisor
from yoga_relief.api import router
from yoga_relief.claude_client import make_anthropic_client
from yoga_relief.config import Settings
from yoga_relief.repository import DATA_DIR, Repository
from yoga_relief.service import AdviceService

STATIC_DIR = Path(__file__).parent / "static"

# 前端沒有 inline script／style、不載外部資源，所以 CSP 可以只允許同源。
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; base-uri 'self'; "
        "form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def create_app(
    *,
    data_dir: Path = DATA_DIR,
    advice_path: Path = DEFAULT_ADVICE_PATH,
    settings: Settings | None = None,
    client=None,
) -> FastAPI:
    settings = settings or Settings()
    repo = Repository.load(data_dir)
    store = AdviceStore.load(advice_path)

    live = None
    if settings.live_ai:
        if client is None:
            client = make_anthropic_client(settings)
        live = LiveAdvisor(client, settings.claude_model)

    # 公開服務不開 /docs、/redoc、/openapi.json，少暴露一點 API 結構
    app = FastAPI(title="Yoga Relief", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        return response

    app.state.settings = settings
    app.state.repo = repo
    app.state.store = store
    app.state.service = AdviceService(repo, store, live)

    app.include_router(router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
