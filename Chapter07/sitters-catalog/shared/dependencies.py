from fastapi import Request

from .infrastructure.base_repository import BaseRepository


async def get_repository(request: Request) -> BaseRepository:
    return request.state.repository
