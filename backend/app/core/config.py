import os
import json
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ApexQuant AI"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = "apexquant_super_secret_jwt_key_change_in_prod_1337"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Database
    DATABASE_URL: str = "postgresql://apex_user:apex_secure_password@localhost:5432/apexquant_db"
    
    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Keys
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

    def load_persisted_settings(self):
        db_url = self.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir and os.path.exists(db_dir):
                config_path = os.path.join(db_dir, "config.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r") as f:
                            data = json.load(f)
                            self.OPENAI_API_KEY = data.get("openai_api_key", self.OPENAI_API_KEY)
                            self.GEMINI_API_KEY = data.get("gemini_api_key", self.GEMINI_API_KEY)
                    except Exception:
                        pass

    def save_persisted_settings(self, openai_key: str, gemini_key: str):
        self.OPENAI_API_KEY = openai_key
        self.GEMINI_API_KEY = gemini_key
        db_url = self.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir and os.path.exists(db_dir):
                config_path = os.path.join(db_dir, "config.json")
                try:
                    with open(config_path, "w") as f:
                        import json as json_lib
                        json_lib.dump({
                            "openai_api_key": openai_key,
                            "gemini_api_key": gemini_key
                        }, f, indent=4)
                except Exception:
                    pass

settings = Settings()
settings.load_persisted_settings()
