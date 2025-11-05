from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = "ZTNA Backend API"
    db_user: str = Field(..., validation_alias="POSTGRES_USER")
    db_password: str = Field(..., validation_alias="POSTGRES_PASSWORD")
    db_host: str = Field(..., validation_alias="POSTGRES_HOST")
    db_port: str = Field(..., validation_alias="POSTGRES_PORT")
    db_name: str = Field(..., validation_alias="POSTGRES_DB")
    secret_key: str = Field(..., validation_alias="SECRET_KEY")
    cors_origin: str = Field(..., validation_alias="CORS_ORIGIN")

settings = Settings()
