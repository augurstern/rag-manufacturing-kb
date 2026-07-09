"""
基础能力接口 —— 健康检查、文件上传、模拟查询
阶段一交付物，后续阶段会逐步替换为正式的 RAG 接口
"""
from fastapi import APIRouter, UploadFile, File

# 导入全局配置
from app.config import settings

# 创建路由实例，tags 用于在 Swagger 文档中给接口分组
router = APIRouter(tags=["基础能力接口"])


# ==================== 接口 1：健康检查 ====================
@router.get("/health", summary="服务健康检查")
def health_check():
    """
    检查服务运行状态，以及 DeepSeek API Key 是否已配置。

    可用性：无需认证，供负载均衡器/监控系统调用。
    """
    return {
        "status": "ok",
        "api_key_configured": settings.api_key_configured,
    }


# ==================== 接口 2：文件上传 ====================
@router.post("/upload", summary="单文件上传")
async def upload_file(file: UploadFile = File(...)):
    """
    接收并暂存上传文件，返回文件名和大小。

    当前阶段一只做基础接收，暂不解析文件内容。
    后续阶段二会接入文档解析（parser）和向量化（embedder）服务。

    限制：文件最大 20MB，仅允许 PDF/DOCX/TXT。
    """
    # 校验文件类型
    import os
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_FILE_TYPES:
        return {
            "status": "error",
            "filename": file.filename,
            "error": f"不支持的文件类型 '{ext}'，允许: {settings.ALLOWED_FILE_TYPES}",
        }

    # 读取文件内容
    file_content = await file.read()
    file_size = len(file_content)

    # 校验文件大小
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        return {
            "status": "error",
            "filename": file.filename,
            "error": f"文件大小 {file_size / 1024 / 1024:.1f}MB 超过限制({settings.MAX_UPLOAD_SIZE_MB}MB)",
        }

    await file.close()

    return {
        "status": "received",
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": file_size,
        "note": "文件已接收，阶段二将接入文档解析与向量化流水线",
    }


# ==================== 接口 3：模拟查询 ====================
@router.get("/query", summary="模拟问答查询")
def simulate_query(q: str):
    """
    接受查询问题，返回模拟回答。

    当前阶段一只做接口占位验证。
    后续阶段二会接入混合检索（retriever）和 LLM 生成（generator）服务。

    参数：
        q (str): 用户输入的问题，必填
    """
    return {
        "question": q,
        "answer": "这是一个模拟回答。阶段二将接入 RAG 检索增强生成能力。",
        "model": "none (模拟)",
    }
