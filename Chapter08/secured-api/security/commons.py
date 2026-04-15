from typing import Literal

from pydantic import BaseModel

Role = Literal["standard", "premium", "gold"]


class UserInfo(BaseModel):
    username: str
    roles: set[Role] = {"standard"}
