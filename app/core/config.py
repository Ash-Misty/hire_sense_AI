from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool

    HOST: str
    PORT: int

    API_PREFIX: str

    SECRET_KEY: str

    DATABASE_URL: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Upload settings
    MAX_UPLOAD_SIZE_MB: int = 5
    UPLOAD_DIR: str = "uploads"

    # Resume parser settings
    PARSER_DEFAULT_SECTION_GAP_LINES: int = 3
    MAX_RESUME_TEXT_CHARS: int = 50000

    # Email settings
    MAILJET_API_KEY: str = ""
    MAILJET_SECRET_KEY: str = ""
    MAIL_FROM_EMAIL: str = ""
    MAIL_FROM_NAME: str = "HireSense AI"
    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()