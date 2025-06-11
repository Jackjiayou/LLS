from fastapi import FastAPI
from app.api.endpoints import items, auth
from app.db.database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(items.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
def read_root():
    return {"Hello": "World"} 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)