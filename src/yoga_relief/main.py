"""建立 FastAPI app：載入資料、組裝 service、掛路由與靜態檔。"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from yoga_relief.advisor import DEFAULT_ADVICE_PATH, AdviceStore, LiveAdvisor
from yoga_relief.api import router
from yoga_relief.config import Settings
from yoga_relief.repository import DATA_DIR, Repository
from yoga_relief.service import AdviceService

STATIC_DIR = Path(__file__).parent / "static"


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
            import anthropic

            client = anthropic.Anthropic(timeout=30.0)
        live = LiveAdvisor(client, settings.claude_model)

    app = FastAPI(title="Yoga Relief")
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
