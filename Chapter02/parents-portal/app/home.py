import secrets
import time
from enum import StrEnum

from cachetools import TTLCache
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

COOKIE_EXPIRATION_TIME = 60


cookies_store = TTLCache(  # type: ignore[var-annotated]
    maxsize=100,
    ttl=COOKIE_EXPIRATION_TIME,
    timer=lambda: time.monotonic(),
)

templates = Jinja2Templates(directory="app/templates")


class Lang(StrEnum):
    EN = "en"
    FR = "fr"
    IT = "it"
    PT = "pt"


@router.get("/home/{lang}", response_class=HTMLResponse)
async def home(
    request: Request,
    lang: Lang,
    name: str = Query(default=""),
):
    request_cookie = request.cookies.get("TRACKING")
    cookie_content = cookies_store.get(request_cookie, "Invalid")

    if cookie_content == "Invalid":
        # create a new cookie
        response_cookie = secrets.token_hex(4)
        cookies_store[response_cookie] = response_cookie
        back = False
    else:
        back = True
        response_cookie = request_cookie  # type: ignore[assignment]

    response = templates.TemplateResponse(
        request=request,
        name=f"home-{lang}.j2",
        context={
            "name": name,
            "back": back,
        },
    )

    response.set_cookie(
        key="TRACKING",
        value=response_cookie,
    )

    return response
