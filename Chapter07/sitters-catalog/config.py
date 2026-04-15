from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class RepositoryType(StrEnum):
    MONGO = "mongo"
    TINYDB_FILE = "tinydb_file"
    TINYDB_MEMORY = "tinydb_memory"


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    db_name: str = "babysitter_catalog"
    app_title: str = "Babysitter Catalog API"
    debug: bool = False

    # Repository configuration
    repository_type: RepositoryType = RepositoryType.TINYDB_FILE
    tinydb_path: str = "data/babysitters_db.json"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
