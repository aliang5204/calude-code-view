from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import settings, conversations, chat, context_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    yield


app = FastAPI(title="AI Chat Web", version="1.0.0", lifespan=lifespan)

# CORS — 仅允许本地前端
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://127.0.0.1:1420"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(settings.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(context_routes.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
