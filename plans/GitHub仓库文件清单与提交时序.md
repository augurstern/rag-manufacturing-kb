# 四个 GitHub 仓库文件清单 & 提交时序

## 仓库一：rag-manufacturing-kb（RAG 知识库）

**当前就是这个仓库**。已经有骨架和 plans 文档。

### 最终文件清单（9 月 16 日时态）

```
rag-manufacturing-kb/
├── README.md
├── CLAUDE.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── test_api_connection.py          # API 连通性测试
│   ├── run_rag.py                      # CLI 全链路验证脚本
│   └── app/
│       ├── __init__.py
│       ├── main.py                     # FastAPI 入口
│       ├── config.py
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── upload.py               # 文档上传
│       │   ├── query.py                # RAG 问答
│       │   ├── history.py              # 审计日志
│       │   └── documents.py            # 文档管理
│       ├── services/
│       │   ├── __init__.py
│       │   ├── parser.py               # 文档解析
│       │   ├── chunker.py              # 分块策略
│       │   ├── embedder.py             # 向量化
│       │   ├── retriever.py            # 混合检索
│       │   ├── generator.py            # LLM 生成
│       │   ├── auditor.py              # 审计日志服务
│       │   └── logger.py               # 日志系统
│       ├── models/
│       │   ├── __init__.py
│       │   └── schemas.py              # Pydantic 模型
│       └── db/
│           ├── __init__.py
│           ├── database.py             # SQLite 连接
│           └── models.py               # ORM 模型
├── backend/tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_chunker.py
│   ├── test_embedder.py
│   ├── test_retriever.py
│   ├── test_generator.py
│   └── test_api.py
├── frontend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py                          # Streamlit 主页面
│   └── pages/
│       ├── upload.py                   # 文档上传页
│       ├── chat.py                     # 问答对话页
│       └── history.py                  # 审计日志页
├── data/
│   └── (5-8份测试文档：pdf/docx/txt)
├── docs/
│   ├── 企业级RAG完整设计方案.md
│   ├── 架构设计文档.md                 # 阶段五写
│   └── 模块实现笔记.md                 # 阶段五写
└── plans/                              # 执行计划（可保留也可放 .claude/
│   ...                                  面试官看到说明你有规划习惯）
```

**总文件数**：约 40 个文件（含 tests 和 data）

### 提交时序（每天或每几天一次 commit）

```
06.30  [阶段一] 项目骨架初始化——目录结构、配置文件、.gitignore、技术文档归档
07.01  [阶段一] 五阶段详细执行计划——每阶段含任务清单、交付物、验收标准
07.04  [阶段一] 补充四项目综合时间线+面试补课清单
        ↑ 以上 3 次 commit 已完成 ↑
        ↓ 以下是后续按日期执行的 ↓
        
07.05  [阶段一] 学习Docker——首个Dockerfile+docker-compose实践笔记
07.08  [阶段一] FastAPI最小应用——health/upload/query三个基础接口+Swagger
07.10  [阶段一] Streamlit聊天界面——模拟对话+st.session_state持久化
07.12  [阶段一] API连通性验证——DeepSeek Chat+Embedding双接口测试通过
        ← Tag v0.1-env-ready
        
07.15  [阶段二] 文档解析器——PyPDF2+python-docx，统一ParsedDocument输出
07.18  [阶段二] 文档解析器——pytesseract OCR扫描件支持+单元测试
07.20  [阶段二] 分块策略——滑动窗口500字/100重叠+元数据绑定
07.23  [阶段二] 分块策略——父子分块(3000/500)+表格行分块+单元测试
07.26  [阶段二] Embedding服务——DeepSeek API+ChromaDB写入验证
07.29  [阶段二] 混合检索——向量检索ChromaDB query Top20
07.31  [阶段二] 混合检索——BM25关键词检索+jieba分词+RRF融合(k=60)
08.02  [阶段二] LLM问答生成——Prompt模板+幻觉抑制+来源引用+CLI端到端验证
        ← Tag v0.2-core-ready
        
08.06  [阶段三] FastAPI后端——文档上传接口+文件校验+解析入库联调
08.09  [阶段三] FastAPI后端——RAG问答接口+流式SSE输出
08.12  [阶段三] SQLite审计日志——documents表+audit_logs表+ORM模型
08.15  [阶段三] FastAPI后端——文档管理+历史查询接口
08.18  [阶段三] Streamlit前端——文档上传页+文件拖拽+进度显示
08.20  [阶段三] Streamlit前端——问答对话页+流式输出+来源引用卡片
08.22  [阶段三] Streamlit前端——审计日志页+首页统计+API集成测试
08.23  [阶段三] 全链路联调——30个测试问题+bug修复+测试报告
        ← Tag v0.3-web-ready
        
08.26  [阶段四] Docker容器化——backend/frontend Dockerfile+docker-compose编排
08.28  [阶段四] 云服务器部署——公网IP访问+docker-compose up验证
08.30  [阶段四] 配置安全——文件白名单+大小限制+请求频率限制+文件名清洗
09.01  [阶段四] 日志系统——Python logging+关键操作日志+按天轮转
09.03  [阶段四] 错误处理——LLM重试+ChromaDB检测+文件解析失败兜底+前端断连提示
09.05  [阶段四] 性能测试——端到端延迟拆解+README完善(5分钟可复现)
        ← Tag v0.4-production
        
09.08  [阶段五] 架构设计文档——系统架构图+数据流图+技术选型说明
09.10  [阶段五] 模块实现笔记——分块策略+混合检索+Prompt工程+踩坑记录
09.12  [阶段五] 代码清理——移除调试print+检查无硬编码密钥
09.14  [阶段五] 演示Demo录制+简历项目描述定稿
09.16  [阶段五] 最终检查+README完善+仓库公开
        ← Tag v1.0-release
```

**commit 总数**：约 35 个，分散在 78 天

---

## 仓库二：react-agent-assistant（Agent 工具调用）

### 最终文件清单

```
react-agent-assistant/
├── README.md                           # ReAct原理+架构图+运行截图
├── .gitignore
├── .env.example
├── requirements.txt
├── agent/
│   ├── __init__.py
│   ├── tools.py                        # 3个工具函数(~60行)
│   ├── react_agent.py                  # ReAct循环核心(~150行)
│   └── run_agent.py                    # CLI交互入口(~30行)
└── tests/
    ├── __init__.py
    └── test_agent.py                   # 3-5个测试用例
```

**总文件数**：11 个文件。代码极简洁。

### 提交时序

```
08.18  [初始化] 项目骨架——仓库结构+tools.py三个工具定义+requirements.txt
08.20  [核心] ReAct循环——Prompt模板+Thought/Action/Observation解析
08.23  [核心] ReAct循环——工具执行调度+最大迭代限制+强制终止逻辑
08.25  [核心] 决策日志——每步iteration/llm_output/parsed记录
08.27  [测试] 单元测试——纯计算/搜索+计算/不需要工具三种场景
08.29  [交互] CLI界面——终端对话+决策日志展示+quit退出
08.31  [测试] 集成测试——10种不同类型任务验证+bug修复
09.02  [文档] README——架构说明+快速开始+运行示例截图
09.04  [优化] 代码整理——注释补充+Prompt微调+最终验证
09.05  [发布] Tag v1.0——最终检查+仓库公开
```

**commit 总数**：约 10 个，分散在 18 天

---

## 仓库三：multi-agent-research（多 Agent 协作）

### 最终文件清单

```
multi-agent-research/
├── README.md                           # Supervisor-Worker架构图+设计思路
├── .gitignore
├── .env.example
├── requirements.txt
├── multi_agent/
│   ├── __init__.py
│   ├── workers.py                      # 3个Worker Prompt定义(~80行)
│   ├── supervisor.py                   # 调度+拆分+汇总(~200行)
│   └── run_supervisor.py               # CLI入口(~40行)
├── tests/
│   ├── __init__.py
│   └── test_supervisor.py              # 3个测试场景
└── docs/
    └── 多Agent架构设计.md              # 完整架构文档(面试展示系统设计能力)
```

**总文件数**：12 个文件。

### 提交时序

```
09.07  [初始化] 项目骨架——3个Worker Prompt+角色定义+输出格式规范
09.09  [核心] Supervisor——任务分析+拆分逻辑(_plan_task)
09.11  [核心] Supervisor——Worker调度+结果汇总(_call_worker+_merge_results)
09.12  [核心] 兜底处理——JSON解析失败降级+默认拆分策略
09.13  [测试] 多种任务测试——调研/分析/撰写不同组合+Prompt调优
09.14  [文档] README+架构图+执行日志示例截图
09.15  [文档] 多Agent架构设计.md——完整版设计文档(含LangGraph对比)
09.16  [发布] Tag v1.0——最终检查+仓库公开
```

**commit 总数**：约 8 个，分散在 10 天

---

## 仓库四：lora-finetune-manufacturing（LoRA 微调）

### 最终文件清单

```
lora-finetune-manufacturing/
├── README.md                           # 训练参数表+微调前后对比截图
├── .gitignore
├── requirements.txt
├── lora_finetune.ipynb                 # Colab Notebook(核心)
├── data/
│   └── manufacturing_qa.json           # 50条训练数据
├── generate_data.py                    # 数据生成脚本(可选)
└── screenshots/                        # 微调前后对比截图
    ├── before_1.png
    ├── after_1.png
    └── ...
```

**总文件数**：约 8 个文件。最轻量的仓库。

### 提交时序

```
09.08  [初始化] 项目骨架——.gitignore+requirements.txt+README草稿
09.09  [数据] 50条制造业客服训练数据——覆盖6个场景
09.10  [核心] Colab Notebook——4bit量化加载+LoRA配置+数据预处理
09.11  [核心] Colab Notebook——训练5epoch+LoRA权重保存
09.12  [评估] 微调前后对比——5个测试问题+截图
09.13  [文档] README——训练参数表+对比截图+快速开始指南
09.14  [发布] Tag v1.0——Notebook整理+仓库公开
```

**commit 总数**：约 7 个，分散在 7 天

---

## 四个仓库一览

| 仓库 | 文件名 | 文件数 | commit 数 | 代码行数 | 时间跨度 |
|------|--------|--------|-----------|----------|----------|
| rag-manufacturing-kb | 最复杂 | ~40 | ~35 | ~2000 | 78天 |
| react-agent-assistant | 极简 | ~11 | ~10 | ~300 | 18天 |
| multi-agent-research | 中等 | ~12 | ~8 | ~350 | 10天 |
| lora-finetune-manufacturing | 最轻 | ~8 | ~7 | ~50+notebook | 7天 |

## 每类文件在简历上的作用

| 文件类型 | 面试官怎么看 |
|----------|------------|
| **README.md** | 第一印象。30秒决定"这个项目值不值得问"。必须有架构图+快速开始 |
| **源码(.py)** | 面试深挖材料。命名清晰、注释合理、没有死代码 |
| **测试(tests/)** | 加分项。有测试 = 有工程习惯，区分"会写脚本"和"做过工程" |
| **docs/架构文档** | 系统设计能力展示。证明你能从架构层面思考 |
| **docker-compose.yml** | 证明你能部署。一键启动比"你先装一堆东西"专业 10 倍 |
| **.env.example** | 证明你知道安全规范。没有 API Key 泄露 |
| **requirements.txt** | 基本配置，必须有 |
| **plans/或执行计划** | 可选。有的话说明做事有条理，面试官一般是开发者会喜欢 |

## 所有仓库的公共 .gitignore

四个仓库共用同一份 .gitignore 模板：

```gitignore
# 环境变量
.env

# Python
__pycache__/
*.py[cod]
*.egg-info/
venv/
.venv/

# 向量数据库(仅项目一)
chroma_db/

# 上传文件(仅项目一)
uploads/

# 模型文件(仅项目四)
*.bin
*.safetensors
*.pt
lora_output/

# IDE
.vscode/
.idea/

# 系统
.DS_Store
Thumbs.db

# 日志
*.log
logs/

# Colab(仅项目四)
.ipynb_checkpoints/
```
