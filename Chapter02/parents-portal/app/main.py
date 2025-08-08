from fastapi import FastAPI, Request
from fastapi.datastructures import URL
from fastapi.responses import RedirectResponse

from app.home import Lang
from app.home import router as home_router

app = FastAPI(
    title="The Portal", description="A portal for the users"
)

app.include_router(home_router)


@app.get("/")
async def root_default(
    request: Request,
):
    return RedirectResponse(
        url=URL(path="home/en", query=request.url.query)
    )


@app.get("/home")
def home_default(
    request: Request,
):
    return RedirectResponse(
        url=URL(path="/home/en", query=request.url.query)
    )


@app.get("/{lang}")
def root(lang: Lang, request: Request):
    return RedirectResponse(
        url=URL(path=f"/home/{lang}", query=request.url.query)
    )
