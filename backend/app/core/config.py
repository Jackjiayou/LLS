from pydantic_settings import BaseSettings
import os
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://myapp:mypassword@119.3.210.173:5432/sales_training"
    SECRET_KEY: str = "your-secret-key-here"  # 用于JWT加密
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # 基础URL配置
    BASE_URL: str = "http://localhost:8000"  # 开发环境
    # BASE_URL: str = "https://ai.dl-dd.com"  # 生产环境

    # 讯飞API配置
    XUNFEI_APP_ID: str = "5f30a0b3"
    XUNFEI_API_KEY: str = "d4070941076c1e01997487878384f6c"
    XUNFEI_API_SECRET: str = "MGYyMzJlYmYzZWVmMjIxZWE4ZThhNzA4"

    # 视频合成API配置
    VIDEO_SYNTHESIS_API_URL: str = "http://106.75.44.55:8000"

    # 向量数据库配置
    VECTOR_DB_PATH: str = "./db/fund_nucleotide_chunk"

    # 文件上传配置
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    STATIC_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")

    BASE_DIR : str= os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    # 上传目录
    UPLOAD_DIR : str= os.path.join(BASE_DIR, "uploads")
    file_path_tts : str= os.path.join(UPLOAD_DIR, 'tts')
    file_path_voice: str = os.path.join(UPLOAD_DIR, 'voice')
    voice_url: str = f"{BASE_URL}/uploads/voice"
    # 其他目录
    STATIC_DIR : str= os.path.join(BASE_DIR, "static")
    LOG_DIR : str= os.path.join(BASE_DIR, "logs")

    class Config:
        env_file = ".env"

settings = Settings() 