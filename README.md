# 制造业内部知识库 RAG 系统

基于 RAG（检索增强生成）技术的制造业集团内部知识库问答系统（精简可运行版）。

## 项目定位

本项目是"真实企业级 RAG 完整落地实施清单"的简化实现版本。完整的企业级设计方案请参考 [docs/企业级RAG完整设计方案.md](docs/企业级RAG完整设计方案.md)。

## 技术栈

| 组件 | 本项目 | 企业级对应 |
|------|--------|-----------|
| 向量库 | ChromaDB | Milvus |
| 大模型 | DeepSeek Chat API | 通义千问 72B 本地部署 |
| Embedding | DeepSeek Embedding API | BGE-M3 私有化 |
| 文档解析 | PyPDF2 + Tesseract | RAGFlow |
| 数据库 | SQLite | PostgreSQL |
| 部署 | Docker Compose 单机 | K8s 集群 |

## 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose
- DeepSeek API Key

### 本地开发

```bash
# 1. 克隆项目
git clone <repo-url>
cd 简历RAG项目

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 3. 安装后端依赖
cd backend
pip install -r requirements.txt

# 4. 安装前端依赖
cd ../frontend
pip install -r requirements.txt

# 5. 启动后端
cd ../backend
uvicorn app.main:app --reload --port 8000

# 6. 新终端，启动前端
cd ../frontend
streamlit run app.py

# 访问 http://localhost:8501
```

### Docker 部署

```bash
docker-compose up -d
# 访问 http://localhost:8501
```

## 项目结构

```
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── routers/   # API 路由（upload, query, history）
│   │   ├── services/  # 核心服务（parser, chunker, embedder, retriever, generator）
│   │   ├── models/    # Pydantic 数据模型
│   │   ├── db/        # SQLite ORM
│   │   └── config.py  # 配置管理
│   └── tests/         # 后端测试
├── frontend/          # Streamlit 前端
│   ├── app.py         # 主页面
│   └── pages/         # 子页面（upload, chat, history）
├── data/              # 测试文档
├── docs/              # 设计文档
└── docker-compose.yml
```

## 开发阶段

详见 [CLAUDE.md](CLAUDE.md) 和 .claude/plans/ 目录下的执行计划。
