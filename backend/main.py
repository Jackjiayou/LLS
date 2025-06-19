from fastapi import FastAPI
from app.api.endpoints import  auth, conversation,practice_info,assistant
from app.db.database import engine, Base
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
import  os
# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(conversation.router, prefix="/conversation", tags=["conversation"])
app.include_router(practice_info.router, prefix="/practice", tags=["practice"])
app.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
# os.makedirs(settings.file_path_voice, exist_ok=True)
# os.makedirs(settings.file_path_tts, exist_ok=True)


# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)