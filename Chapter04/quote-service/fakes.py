import logging

logger = logging.getLogger(__name__)


class FakeQuoteRepository:
    def get_random(self) -> str:
        logger.info("testing connection")
        return "This is a test quote."
