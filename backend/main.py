from fastapi import FastAPI
from app.api.endpoints import items, auth, conversation
from app.db.database import engine, Base
from fastapi.staticfiles import StaticFiles
from app.core.config import settings

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(items.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(conversation.router, prefix="/conversation", tags=["conversation"])

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)