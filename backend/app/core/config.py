from pydantic_settings import BaseSettings
import os
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://myapp:mypassword@119.3.210.173:5432/sales_training"
    SECRET_KEY: str = "your-secret-key-here"  # 用于JWT加密
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days


    # 文件上传配置
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    STATIC_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
    class Config:
        env_file = ".env"

settings = Settings() 