
from pydantic import BaseSettings

class Settings(BaseSettings):
    JIRA_API_URL: str
    JIRA_API_TOKEN: str
    JIRA_USER_EMAIL: str
    JIRA_PROJECT_KEY: str = "LIG"

    class Config:
        env_file = ".env"

settings = Settings()
