from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgres_user: str = "user"
    postgres_password: str = "pass"
    postgres_db: str = "appdb"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    feature_flag_url: str = ""
    feature_flag_api_key: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
