"""HTTP 路由。只做 HTTP ↔ service 的轉換，不放商業邏輯。"""

from fastapi import APIRouter, HTTPException, Request

from yoga_relief.models import AdviceRequest, AdviceResponse, BodyPart
from yoga_relief.service import UnknownBodyPart

router = APIRouter(prefix="/api")


@router.get("/body-parts", response_model=list[BodyPart])
def list_body_parts(request: Request) -> list[BodyPart]:
    return request.app.state.repo.body_parts


@router.post("/advice", response_model=AdviceResponse)
def advice(req: AdviceRequest, request: Request) -> AdviceResponse:
    try:
        return request.app.state.service.advise(req)
    except UnknownBodyPart as e:
        raise HTTPException(status_code=404, detail=f"unknown body part: {e.args[0]!r}") from e
