# 项目三（简化版）：多 Agent 协作系统

**定位**：RAG 和 Agent 之后的拔高项目。实际写一个极简 Supervisor + Worker 架构，简历上写完整 LangGraph 版，靠大量补课背住面试细节。
**实际代码量**：~200-300 行 Python
**时间**：1.5 周（09.07 — 09.16），约 20-25 工时

---

## 实际做的 vs 简历写的

| 维度 | 实际代码（你做的） | 简历描述（背的） |
|------|-------------------|-----------------|
| 调度框架 | 手写 Supervisor 调度逻辑 | LangGraph 状态图编排 |
| Worker 数量 | 3 个（不同 System Prompt） | 3 个专职 Agent（CrewAI 角色定义） |
| 通信方式 | 函数返回值（Python dict） | A2A 结构化 JSON Schema |
| 消息队列 | 无（同步顺序执行） | RabbitMQ 异步分发 |
| 大模型 | DeepSeek API | LLaMA 3 本地部署 + vLLM |
| 异常处理 | 简单 try/except | 任务中断续跑、失败回滚 |
| 人工介入 | 无 | 分级权限 + 人工确认开关 |

---

## 架构概览（你实际做的）

```
用户任务
    │
    ▼
┌─────────────────────┐
│  Supervisor Agent   │  ← 一个 System Prompt
│  "拆分任务+分配"    │
└──────┬──────────────┘
       │ 拆成 3 个子任务
       │
       ├──→ Worker 1: 调研 Agent ──→ 搜索结果
       │    System Prompt: "你是一个行业调研专家..."
       │
       ├──→ Worker 2: 分析 Agent ──→ 分析报告
       │    System Prompt: "你是一个数据分析师..."
       │
       └──→ Worker 3: 撰写 Agent ──→ 最终报告
            System Prompt: "你是一个报告撰写专家..."
       │
       ▼
┌─────────────────────┐
│  Merge Agent        │  ← 汇总 3 个 Worker 的输出
│  "整合成最终报告"    │
└─────────────────────┘
       │
       ▼
   最终输出
```

本质就是：**用一个 LLM 拆分任务 → 用不同 System Prompt 调用同一个 LLM 做不同的事 → 再用一个 LLM 汇总**。没有状态图、没有消息队列、没有本地模型。

但面试时你讲的是 LangGraph 版的完整架构——两者在"概念"层面是通的，只是实现方式不同。

---

## 任务清单

### 3.1 理解多 Agent 概念（1 天，只看不写）

**关键概念**：

| 概念 | 简单解释 |
|------|----------|
| Supervisor（调度者） | 接收总任务 → 拆分子任务 → 分配给 Worker → 检查结果 → 汇总 |
| Worker（执行者） | 接收子任务 → 用自己领域的专业知识完成 → 返回结果给 Supervisor |
| A2A 通信 | Agent-to-Agent，Agent 之间传递消息的方式。最简单是 Python dict，生产用 JSON Schema |
| 任务分解 | 把一个复杂任务拆成多个独立子任务。关键是"拆得开、合得拢" |
| 结果汇总 | 把多个 Worker 的输出合并成一个完整答案。可能需要去重、去冲突、统一格式 |

**需要看的资料**（花 2-3 小时）：
- LangGraph 官方 Quick Start（只理解概念，不需要会写代码）
- CrewAI 官方文档的前两页（理解 Role/Goal/Backstory 的定义方式）
- 1-2 篇中文博客讲"多 Agent 协作架构"

---

### 3.2 定义 Worker Agent 的 System Prompt（1 天）

**文件**：`multi_agent/workers.py`

三个 Worker，本质就是三个不同的 System Prompt。你不需要跑三个不同的模型——都用 DeepSeek API，只改 System Prompt。

```python
# Worker 1: 调研 Agent
RESEARCHER_PROMPT = """你是一个行业调研专家。你的任务是搜索和收集信息。

## 你的能力
- 快速定位关键信息
- 从多个来源交叉验证
- 区分事实和观点

## 输出格式
请按以下结构输出：
1. **关键发现**：列出 3-5 条最重要的信息
2. **数据来源**：每条信息标注来源
3. **信息可信度**：高/中/低，并说明原因

## 注意
- 不要编造信息
- 如果不确定，标注"待验证"
"""

# Worker 2: 数据分析 Agent
ANALYST_PROMPT = """你是一个数据分析师。你的任务是对提供的数据进行量化分析。

## 你的能力
- 提取关键指标
- 计算增长率和占比
- 发现数据趋势和异常

## 输出格式
请按以下结构输出：
1. **核心指标**：列出关键数据点
2. **趋势分析**：对比、增长率、变化方向
3. **异常发现**：如果数据中有异常值，指出并分析可能原因
4. **结论**：用数据支撑的 1-2 句话总结

## 注意
- 计算过程要可复现
- 保留原始数据，标注你做了哪些计算
"""

# Worker 3: 报告撰写 Agent
WRITER_PROMPT = """你是一个专业报告撰写专家。你的任务是将碎片化信息整合成结构化的报告。

## 你的能力
- 将多个来源的信息组织成逻辑清晰的报告
- 使用恰当的小标题和段落结构
- 确保语言专业、结论有依据

## 输出格式
请按以下结构输出：
1. **摘要**：一段话概括全文
2. **正文**：分章节展开
3. **结论与建议**：基于前文给出 actionable 的建议

## 注意
- 标注所有引用的来源
- 不要添加原文中没有的信息
"""

# Worker 配置
WORKERS = {
    "researcher": {
        "name": "调研 Agent",
        "prompt": RESEARCHER_PROMPT,
        "description": "搜索和收集信息",
    },
    "analyst": {
        "name": "分析 Agent",
        "prompt": ANALYST_PROMPT,
        "description": "数据分析和指标提取",
    },
    "writer": {
        "name": "撰写 Agent",
        "prompt": WRITER_PROMPT,
        "description": "报告撰写和内容整合",
    },
}
```

**交付物**：
- [ ] 3 个 Worker 的 System Prompt 写定
- [ ] 每个 Prompt 有明确的"输出格式"要求

---

### 3.3 实现 Supervisor 调度逻辑（3 天）⭐ 核心

**文件**：`multi_agent/supervisor.py`

这是整个项目的核心——手写的任务分发和汇总逻辑：

```python
from openai import OpenAI
from multi_agent.workers import WORKERS
import json

SUPERVISOR_PROMPT = """你是一个项目主管（Supervisor Agent）。你的职责是：
1. 分析用户的任务
2. 将任务拆解为子任务
3. 分配给合适的 Worker Agent
4. 汇总 Worker 的输出，形成最终交付物

## 可用的 Worker Agent
{worker_list}

## 工作流程
1. 先理解用户想要什么
2. 决定需要哪些 Worker（按顺序）
3. 为每个 Worker 写清楚子任务描述
4. Worker 完成后，检查结果质量
5. 如果某个 Worker 的结果不够好，决定是否需要重做
6. 汇总所有 Worker 的输出

## 输出格式
请以 JSON 格式输出任务分解计划：
{{
  "task_summary": "一句话描述总任务",
  "subtasks": [
    {{
      "worker": "researcher",  // 或 analyst / writer
      "description": "这个子任务的具体内容",
      "expected_output": "期望的输出格式"
    }}
  ],
  "execution_order": ["researcher", "analyst", "writer"],
  "merge_strategy": "如何汇总各 Worker 的输出"
}}
"""

class SupervisorAgent:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.execution_log = []  # 完整的执行日志（面试展示用）

    def run(self, task: str) -> dict:
        """接收总任务，协调 Worker 完成"""
        self.execution_log = []
        
        # 步骤 1: 理解任务 + 拆分
        self.execution_log.append({"step": "任务分析", "status": "开始"})
        plan = self._plan_task(task)
        self.execution_log.append({
            "step": "任务分析",
            "status": "完成",
            "detail": plan
        })
        
        # 步骤 2: 按顺序执行子任务
        worker_results = {}
        for subtask in plan["subtasks"]:
            worker_name = subtask["worker"]
            self.execution_log.append({
                "step": f"Worker执行",
                "worker": worker_name,
                "status": "开始",
                "task": subtask["description"]
            })
            
            # 调用 Worker（就是换了 System Prompt 的 LLM 调用）
            result = self._call_worker(worker_name, subtask["description"])
            worker_results[worker_name] = result
            
            self.execution_log.append({
                "step": f"Worker执行",
                "worker": worker_name,
                "status": "完成",
                "result_preview": result[:100] + "..."
            })
        
        # 步骤 3: 汇总结果
        self.execution_log.append({"step": "结果汇总", "status": "开始"})
        final_report = self._merge_results(task, worker_results, plan["merge_strategy"])
        self.execution_log.append({"step": "结果汇总", "status": "完成"})
        
        return {
            "task": task,
            "plan": plan,
            "worker_results": worker_results,
            "final_report": final_report,
            "execution_log": self.execution_log,
        }

    def _plan_task(self, task: str) -> dict:
        """让 Supervisor LLM 拆分任务"""
        worker_list = "\n".join([
            f"- {name}: {info['description']}"
            for name, info in WORKERS.items()
        ])
        
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SUPERVISOR_PROMPT.format(worker_list=worker_list)},
                {"role": "user", "content": f"请分析以下任务并制定执行计划：\n{task}"},
            ],
            temperature=0.1,
        )
        
        reply = response.choices[0].message.content
        # 尝试提取 JSON 部分
        try:
            # 简单处理：找到 { 开始 } 结束的部分
            start = reply.find("{")
            end = reply.rfind("}") + 1
            plan = json.loads(reply[start:end])
        except json.JSONDecodeError:
            # 如果 LLM 没按 JSON 格式输出，兜底处理
            plan = {
                "task_summary": task,
                "subtasks": [
                    {"worker": "researcher", "description": f"搜索关于「{task}」的信息"},
                    {"worker": "analyst", "description": f"分析关于「{task}」的数据"},
                    {"worker": "writer", "description": f"撰写关于「{task}」的报告"},
                ],
                "execution_order": ["researcher", "analyst", "writer"],
                "merge_strategy": "按调研→分析→撰写的顺序整合",
            }
        return plan

    def _call_worker(self, worker_name: str, task: str) -> str:
        """用 Worker 的 System Prompt 调用 LLM"""
        if worker_name not in WORKERS:
            return f"错误：未知 Worker '{worker_name}'"
        
        worker = WORKERS[worker_name]
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": worker["prompt"]},
                {"role": "user", "content": task},
            ],
            temperature=0.3,  # Worker 可以稍高，保留一点创造性
        )
        return response.choices[0].message.content

    def _merge_results(self, task: str, worker_results: dict, merge_strategy: str) -> str:
        """汇总所有 Worker 的输出"""
        merge_prompt = f"""你是项目主管。请将以下 Worker Agent 的输出整合成一份完整的最终报告。

## 原始任务
{task}

## 汇总策略
{merge_strategy}

## Worker 输出
"""
        for name, result in worker_results.items():
            merge_prompt += f"\n### {WORKERS[name]['name']} 的输出：\n{result}\n"
        
        merge_prompt += "\n## 要求\n请整合成一份结构化报告，包含：摘要、正文、结论与建议。标注各部分信息来自哪个 Worker。"

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": merge_prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content
```

**设计决策笔记**（面试用）：

> **为什么手写 Supervisor 而不是用 LangGraph？**
> 核心的多 Agent 协作逻辑其实就三个步骤：拆分→执行→汇总。用 LangGraph 实现需要定义 StateGraph、节点、条件边、Checkpoint，代码量至少要 500 行。手写 200 行就能跑通，而且逻辑更透明——能精确看到 Supervisor 每一步在做什么。理解了底层逻辑后，用 LangGraph 只是换一种组织代码的方式。

> **Worker 之间为什么是串行而不是并行？**
> 实际业务中，调研→分析→撰写有先后依赖关系（分析依赖调研结果，撰写依赖分析结论）。如果 Worker 之间没有依赖，可以并行。但这个项目三个 Worker 是链条关系，串行是正确的。LangGraph 里通过条件边实现这种依赖。

> **LLM 输出的 JSON 解析失败怎么办？**
> 这是多 Agent 系统最常见的坑——LLM 输出的格式不可控。我做了一个兜底方案：如果 JSON 解析失败，用默认的任务拆分策略（三个 Worker 各做一个方面）。生产环境中更好的做法是：1）用 Function Calling 强制 LLM 输出结构化 JSON；2）加入格式校验层，不合法就重试。

**CLI 验证脚本** `multi_agent/run_supervisor.py`：

```python
from multi_agent.supervisor import SupervisorAgent
from dotenv import load_dotenv
import os

load_dotenv()

supervisor = SupervisorAgent(api_key=os.getenv("DEEPSEEK_API_KEY"))

task = "帮我调研一下2024年国内新能源汽车市场，分析主要品牌的市场份额变化趋势，并写一份简要的报告"

print(f"📋 任务: {task}\n")
print("🔄 多 Agent 集群工作中...\n")

result = supervisor.run(task)

print("=" * 60)
print("📊 最终报告:")
print("=" * 60)
print(result["final_report"])

print("\n" + "=" * 60)
print("📝 执行日志:")
print("=" * 60)
for log in result["execution_log"]:
    print(f"  [{log['step']}] {log.get('status', '')} {log.get('worker', '')}")
```

**交付物**：
- [ ] `supervisor.py` 完成（~200 行）
- [ ] `workers.py` 完成（~90 行）
- [ ] CLI 脚本可跑通：输入一个调研任务，输出完整报告
- [ ] 执行日志完整记录

---

### 3.4 测试与调优（1 天）

**测试场景**（至少跑 3 个不同的任务）：

| 测试任务 | 预期行为 |
|----------|----------|
| "调研新能源汽车市场并写报告" | 调研→分析→撰写，三步依次执行 |
| "分析这份销售数据并给出建议"（附数据文件） | 跳过调研，直接分析→撰写 |
| "帮我写一份简历"（不需要调研和分析） | Supervisor 应该只调用 Writer |

**注意观察**：
- Supervisor 拆分的子任务是否合理？
- Worker 输出是否符合格式要求？
- 最后汇总的报告质量如何？
- 有没有 Worker 收到不合适的任务？

**调优提示**：
- 如果 Supervisor 拆分不合理，调整 SUPERVISOR_PROMPT
- 如果 Worker 输出格式混乱，给每个 Worker 的 Prompt 加更具体的格式要求
- 如果最后汇总报告太水，给 Merge Prompt 加"必须引用各 Worker 的具体发现"

**交付物**：
- [ ] 至少 3 个不同类型的测试任务跑通
- [ ] 记录每个任务的执行日志和最终输出
- [ ] 记录发现的 Prompt 问题和改进

---

### 3.5 代码整理 + README（0.5 天）

**文件**：`multi_agent/README.md`

简短的 README + 一个 Mermaid 架构图。

---

## 项目三时间分配

```
Day 1 (自习日): 理解多 Agent 概念 + 看 LangGraph/CrewAI 文档
Day 2 (晚间)  : 写 3 个 Worker 的 System Prompt
Day 3 (晚间)  : 实现 Supervisor._plan_task（任务拆分）
Day 4 (自习日): 实现 Supervisor._call_worker + _merge_results
Day 5 (晚间)  : CLI 脚本 + 第一个完整测试
Day 6 (晚间)  : 用不同任务测试 + 调 Prompt
Day 7 (晚间)  : 整理代码 + README
Day 8 (自习日): 补课（LangGraph 概念 + Agent 通信协议笔记）
```

---

## 项目三结束验收

- [ ] `workers.py` — 3 个 Worker Prompt 定义
- [ ] `supervisor.py` — Supervisor 调度逻辑（拆分→执行→汇总）
- [ ] `run_supervisor.py` — CLI 可执行
- [ ] 至少 3 个不同类型的测试任务跑通
- [ ] 执行日志完整
- [ ] README 完成
- [ ] 补课笔记完成（LangGraph 概念 + 通信协议 + 故障处理）

**完成后填写**：
- 实际完成日期：_____
- 用时：_____ 小时
- 调 Prompt 花的时间最多的环节：
- 面试可以讲的多 Agent 协作故事：
