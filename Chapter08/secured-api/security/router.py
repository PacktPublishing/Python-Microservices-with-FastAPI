from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[
        OAuth2PasswordRequestForm, Depends()
    ],
    request: Request,
) -> Token:
    authenticator = request.state.authenticator
    access_token = await authenticator.generate_user_token(
        form_data.username, form_data.password
    )
    return Token(
        access_token=access_token, token_type="bearer"
    )
