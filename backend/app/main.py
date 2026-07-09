"""
FastAPI 应用入口 —— 制造业内部知识库 RAG 系统后端
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入路由模块
from app.routers.base_api import router as base_router

# 创建 FastAPI 应用实例
app = FastAPI(
    title="制造业内部知识库RAG API",
    version="0.1.0",
    description="基于 FastAPI 构建的 RAG 问答后端服务——支持文档上传、智能检索、AI问答",
)

# CORS 中间件：允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段全放通，生产环境需限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(base_router, prefix="/api/v1")


@app.get("/")
def root():
    """根路径——API 服务入口"""
    return {
        "service": "制造业内部知识库RAG API",
        "version": "0.1.0",
        "docs": "/docs",
    }
