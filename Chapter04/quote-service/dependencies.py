import logging
from typing import Annotated

from fastapi import Depends
from repository import QuoteRepository

logger = logging.getLogger(__name__)

_repository = QuoteRepository()


def get_quote_repository() -> QuoteRepository:
    return _repository


QuoteRepositoryDep = Annotated[
    QuoteRepository, Depends(get_quote_repository)
]


class LoggedQuoteService:
    def __init__(self, repository: QuoteRepository) -> None:
        self.repository = repository

    def random_quote(self) -> str:
        quote = self.repository.get_random()
        logger.info("Served quote: %s", quote)
        return quote


def get_logged_quote_service(
    repository: QuoteRepositoryDep,
) -> LoggedQuoteService:
    return LoggedQuoteService(repository)


LoggedQuoteServiceDep = Annotated[
    LoggedQuoteService,
    Depends(get_logged_quote_service),
]
