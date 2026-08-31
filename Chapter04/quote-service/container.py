from dependency_injector import containers, providers
from repository import QuoteRepository


class Container(containers.DeclarativeContainer):
    quote_repository = providers.Singleton(QuoteRepository)
