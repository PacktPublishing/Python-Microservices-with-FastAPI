from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    jwt_secret_key: str = "4f8e2b6a1c9d3f7e5a0b8c2d6e4f1a9b"
    session_secret_key: str = "1a3c5e7f9b0d2e4f6a8c0e2f4a6b8d0c"
    github_client_id: str
    github_client_secret: str


settings = Settings()
