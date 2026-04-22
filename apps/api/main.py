import logging

from app.api.v1 import assets, auth, chat, knowledge, risk, strategy
from app.core.config import settings
from app.core.redis import ping_redis, redis_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Solon AI - Solana生态AI金融智能体后端API",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["资产"])
app.include_router(strategy.router, prefix="/api/v1/strategy", tags=["策略"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["AI对话"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["风控"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["知识库"])


@app.get("/")
async def root():
    return {"message": "Solon AI API", "version": settings.VERSION, "docs": "/docs"}


@app.get("/health")
async def health_check():
    redis_ok = await ping_redis()
    return {
        "status": "healthy" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
    }


@app.on_event("shutdown")
async def shutdown_event():
    await redis_client.aclose()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
