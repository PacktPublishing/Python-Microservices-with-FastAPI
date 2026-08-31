import sys
from typing import Annotated

from dependencies import LoggedQuoteServiceDep, QuoteRepositoryDep
from dependency_injector.wiring import Provide, inject
from fastapi import BackgroundTasks, Depends, FastAPI
from repository import QuoteRepository

from container import Container

app = FastAPI()
container = Container()


@app.get("/quote")
def get_quote(repository: QuoteRepositoryDep) -> dict[str, str]:
    return {"quote": repository.get_random()}


@app.get("/quote/logged")
def get_logged_quote(
    service: LoggedQuoteServiceDep,
) -> dict[str, str]:
    return {"quote": service.random_quote()}


@app.get("/quotes/count")
@inject
async def count_quotes(
    repository: Annotated[
        QuoteRepository,
        Depends(Provide[Container.quote_repository]),
    ],
) -> dict[str, int]:
    return {"count": len(repository.quotes)}


def log_quote_served(quote: str) -> None:
    """Write to a log file after the response is sent."""
    with open("served.log", "a") as f:
        f.write(f"{quote}\n")


@app.get("/quote/async")
def get_quote_with_logging(
    repository: QuoteRepositoryDep,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    quote = repository.get_random()
    background_tasks.add_task(log_quote_served, quote)
    return {"quote": quote}


container.wire(modules=[sys.modules[__name__]])
