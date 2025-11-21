from typing import List
from pydantic import Field, AnyHttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str = Field(..., validation_alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., validation_alias="POSTGRES_PASSWORD")
    POSTGRES_HOST: str = Field(..., validation_alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(..., validation_alias="POSTGRES_PORT")
    POSTGRES_DB: str = Field(..., validation_alias="POSTGRES_DB")
    CORS_ORIGINS: List[AnyHttpUrl] = Field(default_factory=list, validation_alias="CORS_ORIGIN")

    OIDC_ISSUER: AnyHttpUrl = Field(..., validation_alias="OIDC_ISSUER")
    OIDC_CLIENT_ID: str = Field(..., validation_alias="OIDC_CLIENT_ID")
    OIDC_CLIENT_SECRET: str | None = Field(default=None, validation_alias="OIDC_CLIENT_SECRET")
    OIDC_JWKS_URI: AnyHttpUrl = Field(..., validation_alias="OIDC_JWKS_URI")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    LOG_LEVEL: str = "INFO"
    DEFAULT_USER_ROLE: str = Field(default="dpa-device", validation_alias="DEFAULT_USER_ROLE")
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {
        "case_sensitive": True,
        "arbitrary_types_allowed": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    def model_post_init(self, __context: dict) -> None:
        if isinstance(self.CORS_ORIGINS, str):
            self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
