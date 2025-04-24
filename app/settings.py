from pydantic_settings import BaseSettings

class APISettings(BaseSettings):
    APP_VERSION: str = "0.0.1"
    APP_NAME: str = "AI Art Therapy"
    API_PREFIX: str = ""
    IS_DEBUG: bool=True

    class Config:
        env_file = '.env', '.env.prod', '.env.local'
        extra = "ignore"