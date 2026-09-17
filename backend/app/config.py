from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "ParcelWalaa API"
    environment: str = "development"
    database_url: str = "sqlite:///./parcelwala.db"
    jwt_secret_key: str = "unsafe-development-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:3000"
    seed_admin_email: str = "admin@parcelwala.local"
    seed_admin_password: str = "ChangeMe123!"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

settings = Settings()
