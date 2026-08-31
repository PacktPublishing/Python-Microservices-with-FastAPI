import random


class QuoteRepository:
    def __init__(self) -> None:
        self.quotes = [
            "Simplicity is the ultimate sophistication.",
            "Make it work, make it right, make it fast.",
            "Programs must be written for people to read.",
        ]

    def get_random(self) -> str:
        return random.choice(self.quotes)
