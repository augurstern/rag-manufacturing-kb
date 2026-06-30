# 阶段二：核心 RAG 链路打通

**时间**：2026.07.13 — 2026.08.02（21 天，约 90 工时）
**目标**：实现"文档上传 → 解析 → 分块 → 向量化 → 检索 → 问答"的最精简链路，在本地 CLI 跑通。
**里程碑**：5-8 份文档 + 20 个测试问题，检索准确率 ≥80%，CLI 脚本可端到端验证。
**重要性**：⭐⭐⭐⭐⭐ — 整个项目最核心的阶段，面试所有技术问题都围绕这里的模块展开。

---

## 时间分配

```
Week 3 (07.13-07.19): 自习2天[解析器8h+分块8h] + 上课5天[解析器4h+分块8h+embedding3h] = 31h
Week 4 (07.20-07.26): 自习2天[embedding8h+检索8h] + 上课5天[检索15h] = 31h  ← 7.20后时间增多
Week 5 (07.27-08.02): 自习2天[检索4h+生成12h] + 上课5天[生成4h+端到端11h] = 31h

总计约 93h（含缓冲）
```

---

## 为什么阶段二最重要

面试官不会关心你的 Streamlit 页面好不好看，但他们会问：

- "你的分块策略是怎么设计的？为什么用父子分块？"
- "向量检索和关键词检索你是怎么融合的？RRF 的 k 值是多少？"
- "怎么防止 LLM 瞎编答案？你的 Prompt 模板长什么样？"
- "ChromaDB 的索引是怎么建的？检索延迟多少？"

**以上所有问题，答案都在阶段二的代码里。** 所以这个阶段不光要写代码，还要边写边记录设计决策。

---

## 任务清单

### 2.1 文档解析服务 `parser.py`（4 天）

**文件**：`backend/app/services/parser.py`

**功能需求**：

| 文件类型 | 解析方式 | 注意事项 |
|----------|----------|----------|
| 纯文本 PDF | PyPDF2 逐页提取 | 保留页码信息 |
| 扫描件 PDF | pdf2image 转图片 → pytesseract OCR | 需要装 tesseract：`apt install tesseract-ocr tesseract-ocr-chi-sim` |
| Word (.docx) | python-docx 提取段落 + 表格 | 表格内容用 `|` 分隔保留结构 |
| TXT | 直接读取，自动检测编码 | 用 `chardet` 检测 GBK/UTF-8 |

**统一输出数据结构**：

```python
from dataclasses import dataclass

@dataclass
class ParsedDocument:
    title: str           # 文件名（不含扩展名）
    text: str            # 完整提取文本
    pages: list[dict]    # [{"page_num": 1, "text": "..."}, ...]
    source_type: str     # "pdf" | "docx" | "txt" | "scanned_pdf"
    metadata: dict       # {"file_size": xxx, "page_count": n, ...}
```

**设计决策记录**（面试会问）：

> **Q: 为什么不用 LangChain 的 Document Loader？**
> A: LangChain 封装的 Loader 对中文扫描件支持不好，而且出问题时难以调试。手写解析器能精确控制每一层的输出，出问题能定位到具体步骤。理解了底层原理后，未来用 LangChain 也只是换个调用方式。

**单元测试**（`backend/tests/test_parser.py`）：
- 准备 1 个纯文本 PDF、1 个 Word 文档、1 个 TXT 文件
- 验证 ParsedDocument 的 text 不为空
- 验证 page_count 正确
- 验证表格内容保留

**交付物**：
- [ ] `parser.py` 代码完成
- [ ] 3 个测试文件准备就绪
- [ ] 单元测试全部通过
- [ ] `[阶段二] 实现文档解析器——支持PDF/Word/TXT，含扫描件OCR`

---

### 2.2 分块策略服务 `chunker.py`（4 天）⭐ 面试核心

**文件**：`backend/app/services/chunker.py`

**三种分块策略**：

```python
# 策略一：普通文字文档分块
# 500 字符/块，相邻块重叠 100 字符
# 原因：500 字是 Embedding 模型的最佳语义表达区间；100 字重叠防止关键信息落在边界被切断

# 策略二：父子分块（工艺/维修手册专用）
# 父块：3000 字符，步长 1500（用于向量检索，保证语义完整）
# 子块：500 字符（送入 LLM 生成答案，保证精确聚焦）
# 检索流程：用户问题 → 匹配父块 → 返回对应子块列表 → 送入 LLM
# 原因：设备维修手册通常一个故障描述跨多段，3000 字能覆盖完整故障描述+处理步骤；
#       但 LLM 上下文窗口有限，只送最相关的 500 字子块

# 策略三：表格行分块
# 检测到表格行（含 | 分隔符），按行独立分块
# 每行携带表头信息，避免参数混淆
# 原因：零部件参数表中每行是一个独立部件，合并分块会导致检索时"张冠李戴"
```

**元数据绑定**（每个 Chunk 携带）：

```python
{
    "source_file": "XX设备维修手册.pdf",
    "page_number": 12,
    "chunk_index": 5,
    "chunk_strategy": "parent_child",  # 或 "sliding_window" / "table_row"
    "parent_chunk_id": "doc1_p12_c0",  # 父子分块时标记父块
    "doc_type": "manual",
    "char_count": 487,
}
```

**设计决策记录**（面试会问）：

> **Q: 为什么 chunk_size 选 500 而不是 256 或 1024？**
> A: 256 对中文来说太短（约 150 个汉字），语义碎片化严重；1024 太宽，检索精度下降。
>    500 字符≈300 汉字，刚好表达一个完整语义单元。这是参考 BGE-M3 论文的推荐范围
>    并结合制造业文档的特点（短句多、参数密集）做的调整。

> **Q: 父子分块和普通分块在什么场景下分别使用？**
> A: 普通文档（新闻、规范、通知）用 500 窗口分块即可。
>    维修手册和工艺文档用父子分块——这类文档的特点是"一个问题的完整描述跨多个段落"，
>    用 500 字检索容易"看到一半"，父子分块保证了检索到的上下文是完整的。

**单元测试**（`backend/tests/test_chunker.py`）：
- 构造 1000 字文本，验证分块数量、每块大小、重叠是否正确
- 构造表格文本，验证行分块正常
- 构造 5000 字长文，验证父子分块逻辑

**交付物**：
- [ ] `chunker.py` 代码完成（三种策略）
- [ ] 单元测试全部通过
- [ ] 分块设计决策文档（几句笔记即可，面试用）

---

### 2.3 Embedding 向量化服务 `embedder.py`（3 天）

**文件**：`backend/app/services/embedder.py`

**方案选择**：
- **方案 A（推荐，先用这个）**：DeepSeek Embedding API
  - 优点：效果最好，4096 维，0.25 元/百万 token，月成本可控
  - 缺点：依赖外网 API
- **方案 B（备选，A 不行再试）**：BGE-small-zh 本地运行
  - 优点：完全离线、免费
  - 缺点：384 维（效果弱于 4096），需额外安装 `sentence-transformers`，占内存约 500MB

**ChromaDB 集成**：

```python
import chromadb

# 初始化客户端（持久化模式）
client = chromadb.PersistentClient(path="./chroma_db")

# 创建或获取 collection
collection = client.get_or_create_collection(
    name="manufacturing_knowledge",
    metadata={"hnsw:space": "cosine"},  # 余弦相似度
)

# 写入向量
collection.add(
    ids=[f"doc1_p1_c0", "doc1_p1_c1", ...],
    documents=[chunk_text_0, chunk_text_1, ...],
    metadatas=[meta_0, meta_1, ...],
    embeddings=[vec_0, vec_1, ...],  # DeepSeek API 返回的向量
)
```

**关键注意点**：
- ChromaDB 默认使用 HNSW 索引，`cosine` 距离适合语义搜索
- `ids` 必须全局唯一，格式：`{filename}_{page}_{chunk_index}`
- 持久化路径 `./chroma_db` 已在 `.gitignore` 中排除

**单元测试**（`backend/tests/test_embedder.py`）：
- 调用 API 获取 1 条 embedding，验证维度正确（4096）
- 写入 ChromaDB，用 `collection.get()` 读回验证
- 批量写入 10 条，验证查询返回正确数量

**交付物**：
- [ ] `embedder.py` 代码完成
- [ ] ChromaDB 读写验证通过
- [ ] 单元测试全部通过

---

### 2.4 混合检索服务 `retriever.py`（5 天）⭐ 面试核心

**文件**：`backend/app/services/retriever.py`

**检索架构**：

```
用户问题
    │
    ├──→ 向量检索 (ChromaDB query) → Top 20
    │        问题向量化 → cosine 相似度 → 排序
    │
    ├──→ 关键词检索 (jieba + BM25) → Top 20
    │        问题分词 → BM25 倒排索引 → 排序
    │
    ▼
  RRF 融合 (Reciprocal Rank Fusion)
    RRF_score(d) = Σ 1/(k + rank_i(d))
    k = 60（平滑参数，业界常用值）
    │
    ▼
  Top 20 融合结果
    │
    ├──→ 轻量重排 (可选：BGE-Reranker 或 LLM 打分)
    │       对 Top 20 逐条打分，选 Top 6
    │
    ▼
  最终 Top 6 Chunk + 元数据
```

**BM25 实现要点**：

```python
from rank_bm25 import BM25Okapi
import jieba

# 对每个 chunk 做中文分词
tokenized_chunks = [list(jieba.cut(chunk)) for chunk in all_chunks]

# 构建 BM25 索引
bm25 = BM25Okapi(tokenized_chunks)

# 检索
tokenized_query = list(jieba.cut(question))
bm25_scores = bm25.get_scores(tokenized_query)
```

**RRF 融合代码**：

```python
def rrf_fusion(vector_results, bm25_results, k=60):
    """RRF 融合两路检索结果"""
    scores = {}
    for rank, (chunk_id, _) in enumerate(vector_results):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
    for rank, (chunk_id, _) in enumerate(bm25_results):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
    # 按 RRF 分数降序排列
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**设计决策记录**（面试会问）：

> **Q: 为什么混合检索比纯向量检索好？**
> A: 向量检索基于语义相似度，对专业术语可能出现"近义但不精确"的问题。
>    比如搜索"轴承座"，向量检索可能返回"轴承盖"（语义相近但不同部件），
>    而 BM25 精确匹配能保证"轴承座"这个关键词的精确命中。
>    两路融合 = 语义理解 + 关键词精确匹配，互为补充。

> **Q: RRF 和加权求和有什么区别？为什么用 RRF？**
> A: 加权求和需要先归一化两路分数（向量相似度是 0-1，BM25 分数范围不固定），
>    归一化方式会显著影响结果。RRF 只用排名而非分数，天然消除了量纲差异，
>    不需要调超参。k=60 是学术界常用值，使排名靠后的文档也有非零贡献。

**单元测试**（`backend/tests/test_retriever.py`）：
- 准备 10 个测试文档的 chunk 集合
- 构造 5 个已知答案的查询
- 验证 Top 5 检索结果中包含正确答案的比例

**交付物**：
- [ ] `retriever.py` 代码完成（向量 + BM25 + RRF）
- [ ] 单元测试通过，检索准确率 ≥80%
- [ ] RRF 融合设计笔记

---

### 2.5 LLM 问答生成 `generator.py`（3 天）⭐ 面试核心

**文件**：`backend/app/services/generator.py`

**Prompt 模板**（这是面试最常被问到的）：

```python
SYSTEM_PROMPT = """你是一个制造业集团内部知识库助手。你的职责是帮助员工快速查找设备维修、
操作规程、零部件参数等内部技术资料。

## 回答规则（必须严格遵守）

1. **仅使用提供的文档内容回答**
   - 你的回答必须完全基于下方【参考文档】中的内容
   - 绝对禁止使用你自己的知识、训练数据或常识来补充
   - 如果文档内容不足以回答，请明确说"抱歉，当前知识库中暂无相关信息"

2. **回答末尾必须附上来源引用**
   - 格式：[来源] 《文档名称》第X页
   - 如果引用了多个文档，分别列出

3. **回答风格**
   - 简洁、专业、结构化（适合制造业技术人员阅读）
   - 如果回答包含操作步骤，使用编号列表
   - 如果回答包含参数，使用表格或分点列出

4. **禁止行为**
   - 禁止编造设备型号、参数值、操作步骤
   - 禁止推测文档未提及的内容
   - 禁止使用"根据经验""一般来说"等模糊表述

## 参考文档

{context}

## 用户问题

{question}

## 回答
"""
```

**幻觉抑制机制**：

```python
# 简单规则检测：回答中出现的专业术语是否在 context 中
# 如果术语不在 context 中 → 标记 warning
def check_hallucination(answer: str, context: str) -> list[str]:
    """检查回答中可能存在的幻觉"""
    # 提取回答中的专业名词（简单规则：引号内、大写缩写、数字+单位组合）
    # 检查是否在 context 中出现
    # 返回未匹配的术语列表
    ...
```

**API 调用**：

```python
from openai import OpenAI

client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT.format(context=context, question=question)},
    ],
    temperature=0.3,       # 低温度降低随机性，减少幻觉
    max_tokens=1024,
)
```

**设计决策记录**（面试一定会问）：

> **Q: temperature 为什么设 0.3 而不是 0 或 1？**
> A: temperature=0 会让回答过于机械化、模板化，不适合自然对话。
>    temperature=0.3 在保持回答稳定性的同时有一点灵活性，适合知识库问答场景。
>    生产环境中这个值需要通过 A/B 测试来确定最优值。

> **Q: 为什么不直接用 LangChain 的 RetrievalQA？**
> A: 手写 Prompt 能精确控制 AI 的行为边界（4 条规则明确规定了能做什么不能做什么），
>    LangChain 的默认 Prompt 太泛化，不满足制造业对精确性的要求。
>    理解了底层后，未来用 LangChain 也只是换一个 Prompt 模板而已。

**单元测试**（`backend/tests/test_generator.py`）：
- 构造"有答案"的 context + 问题，验证回答包含文档中的信息
- 构造"无答案"的 context + 问题，验证回答包含"暂无相关信息"
- 验证来源引用格式是否正确

**交付物**：
- [ ] `generator.py` 代码完成（Prompt 模板 + 幻觉检测 + 来源引用）
- [ ] 单元测试全部通过
- [ ] Prompt 设计笔记（为什么设这些规则，面试时展开讲）

---

### 2.6 端到端串联 + CLI 验证（2 天）

**CLI 脚本** `backend/run_rag.py`：

```python
"""RAG 全链路 CLI 验证脚本"""
import sys
sys.path.insert(0, ".")

from app.services.parser import parse_document
from app.services.chunker import chunk_document
from app.services.embedder import embed_and_store
from app.services.retriever import hybrid_search
from app.services.generator import generate_answer

def run_rag(file_path: str, question: str):
    """端到端 RAG 流程"""
    print(f"📄 解析文档: {file_path}")
    doc = parse_document(file_path)

    print(f"✂️ 分块处理: {len(doc.pages)} 页 → 分块中...")
    chunks = chunk_document(doc)

    print(f"🔢 向量化: {len(chunks)} 个 Chunk → ChromaDB")
    embed_and_store(chunks)

    print(f"🔍 混合检索: {question}")
    results = hybrid_search(question, top_k=6)

    print(f"🤖 LLM 生成回答...")
    answer = generate_answer(question, results)

    print(f"\n{'='*50}")
    print(f"📝 问题: {question}")
    print(f"📚 答案: {answer['text']}")
    print(f"📖 来源: {answer['sources']}")
    print(f"⏱️ 耗时: {answer['response_time_ms']}ms")
    return answer

if __name__ == "__main__":
    run_rag("data/pdf/设备维修手册.pdf", "轴承过热怎么办？")
```

**测试文档准备**（5-8 份）：
- 从网上找制造业相关文档：设备说明书、安全操作规范、维修手册
- 建议来源：设备厂家官网技术资料、国家标准（GB 安全规范）、百度文库
- 确保文档用中文，内容覆盖不同文档类型

**测试问题集**（20 个）：

| 类型 | 示例 | 预期行为 |
|------|------|----------|
| 有答案的精确问题 | "XX设备的额定功率是多少？" | 返回文档中的精确值 + 来源 |
| 有答案的操作问题 | "YY故障的处理步骤是什么？" | 返回编号步骤 + 来源 |
| 无答案的问题 | "月球上怎么修设备？" | 返回"暂无相关信息" |
| 模糊问题 | "那个东西坏了怎么办？" | 不编造，尝试反问澄清或如实说信息不足 |
| 专业术语 | "轴承座的公差范围？" | 精确匹配，不混淆相似术语 |

**交付物**：
- [ ] `run_rag.py` CLI 脚本可执行
- [ ] 5-8 份测试文档入库
- [ ] 20 个测试问题跑完，记录结果表格
- [ ] 检索准确率统计 ≥80%

---

## 阶段二每日节奏

```
自习日：集中攻克一个大模块（如解析器、检索服务）
上课日：写单元测试 + 调 bug + 阅读文档 + 优化代码
```

---

## 阶段二最容易踩的坑

| 坑 | 现象 | 解决 |
|----|------|------|
| PyPDF2 读不出中文 | 提取的文本全是乱码 | 检查 PDF 是否扫描件，是的话走 OCR 路径；PyPDF2 对某些中文 PDF 编码支持差 |
| ChromaDB 查询结果为空 | collection.count()=0 或 query 无返回 | 检查 `ids` 是否重复导致覆盖；检查 embedding 是否真的写入了 |
| Embedding API 维度不匹配 | ChromaDB 报错 dimension mismatch | DeepSeek Embedding 不同模型维度可能不同，确认后统一 |
| BM25 分词整段都是单个字 | jieba 对专业术语分词不准 | 添加自定义词典：`jieba.load_userdict("manufacturing_dict.txt")` |
| LLM 回答中编造参数值 | 回答中有文档里不存在的数据 | 降低 temperature；强化 Prompt 约束；检查 context 是否真的包含相关信息 |

---

## 阶段二结束验收

- [ ] `parser.py` — 支持 PDF/Word/TXT，扫描件 OCR
- [ ] `chunker.py` — 三种分块策略全部可用
- [ ] `embedder.py` — DeepSeek API + ChromaDB 读写
- [ ] `retriever.py` — 向量+BM25+RRF 融合，Top 6
- [ ] `generator.py` — Prompt 模板 + 幻觉检测 + 来源引用
- [ ] `run_rag.py` — CLI 端到端可跑通
- [ ] 5-8 份测试文档 + 20 个测试问题
- [ ] 检索准确率 ≥80%
- [ ] Tag `v0.2-core-ready` 已打
- [ ] 每个模块的设计决策笔记已写（分块、检索、Prompt 各几句即可）

**完成后在下面打勾并写上日期**：
- 实际完成日期：___年___月___日
- 用时：_____ 小时
- 检索准确率：_____%
- 遇到的最大困难：
- 如何解决的：
