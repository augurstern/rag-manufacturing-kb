# 项目二（简化版）：单 Agent 工具调用（ReAct 范式）

**定位**：RAG 项目之后的第二个主力项目。实际写一个极简 ReAct Agent，简历上写完整版，靠补课背住面试细节。
**实际代码量**：~200-300 行 Python
**时间**：2 周（08.24 — 09.06），约 25-30 工时

---

## 实际做的 vs 简历写的

| 维度 | 实际代码（你做的） | 简历描述（背的） |
|------|-------------------|-----------------|
| 框架 | 手写 ReAct 循环 | LangChain AgentExecutor |
| 工具数量 | 3 个（搜索 + 计算 + 文件读） | 自定义工具集（含 SQL 查询、Python 执行） |
| 记忆 | 单轮 messages 列表 | Redis 短期 + 向量库长期双记忆 |
| 安全 | 无 | Docker 沙箱隔离 |
| 输出格式 | 自然语言 | 强制 JSON Schema |
| 大模型 | DeepSeek API | DeepSeek API / 本地 LLaMA |

---

## 任务清单

### 2.1 理解 ReAct 范式（1 天，只看不写）

**先搞懂概念再写代码**。

ReAct = Reasoning + Acting，核心是 **"思考 → 行动 → 观察 → 再思考"** 的循环：

```
用户: 帮我查一下今天深圳的天气，然后算一下 35 摄氏度等于多少华氏度

Agent 的思考过程：
  Thought: 用户问了两个问题：查天气和温度转换。先查天气。
  Action: web_search
  Action Input: "深圳 今天 天气 气温"
  
  Observation: [搜索引擎返回] 深圳今天晴，气温 35°C...
  
  Thought: 天气查到了。现在要算 35°C = ?°F。公式是 F = C × 9/5 + 32。
  Action: calculator
  Action Input: 35 * 9 / 5 + 32
  
  Observation: 95.0
  
  Thought: 两个任务都完成了，汇总回答。
  Final Answer: 深圳今天晴天，气温 35°C（相当于 95°F）。
```

**要理解的关键概念**：
- Thought / Action / Action Input / Observation / Final Answer 五个标签的含义
- 为什么需要循环？（因为一个任务可能需要多个工具、多次调用）
- 最大迭代次数（防止死循环，通常设 5-10 次）

**资源**：看 ReAct 原始论文的摘要 + Prompt 模板部分（花 1 小时足够），然后看 2-3 篇中文博客。

---

### 2.2 实现工具集（1 天）

**文件**：`agent/tools.py`

只需要 **3 个工具**，不要贪多：

```python
# 工具 1：联网搜索
def web_search(query: str) -> str:
    """搜索互联网，返回前 3 条结果摘要"""
    # 方案 A：用 DuckDuckGo 免费搜索（pip install duckduckgo-search）
    # 方案 B：用 DeepSeek API 模拟搜索（省事但不够真实）
    # 优先选方案 A
    from duckduckgo_search import DDGS
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=3):
            results.append(f"{r['title']}: {r['body']}")
    return "\n".join(results)

# 工具 2：计算器
def calculator(expression: str) -> str:
    """安全地计算数学表达式"""
    # 注意安全：只允许数字和基本运算符
    import re
    if not re.match(r'^[\d\s\+\-\*\/\(\)\.\%]+$', expression):
        return "错误：表达式包含不允许的字符"
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"

# 工具 3：文件读取
def file_reader(file_path: str) -> str:
    """读取本地文本文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 限制返回长度，避免 token 爆炸
        if len(content) > 3000:
            content = content[:3000] + "\n...(内容过长，已截断)"
        return content
    except FileNotFoundError:
        return f"文件不存在: {file_path}"
    except Exception as e:
        return f"读取失败: {e}"
```

**工具描述（给 LLM 看的）**：

```python
TOOL_DESCRIPTIONS = """
你可以使用以下工具：

1. web_search(query: str) -> str
   搜索互联网信息。参数 query 是搜索关键词。
   适用场景：查天气、查新闻、查资料、查数据等需要外部信息的任务。

2. calculator(expression: str) -> str
   计算数学表达式。参数 expression 是数学表达式，如 "35 * 9 / 5 + 32"。
   适用场景：数学计算、单位换算、数据统计等。

3. file_reader(file_path: str) -> str
   读取本地文本文件。参数 file_path 是文件的完整路径。
   适用场景：读取文件内容进行分析、整理、总结等。
"""
```

**交付物**：
- [ ] 3 个工具函数，每个 < 20 行
- [ ] 每个工具有 docstring 描述
- [ ] 手动测试每个工具：`web_search("深圳天气")`、`calculator("1+1")`、`file_reader("test.txt")`

---

### 2.3 实现 ReAct 循环（3 天）⭐ 核心

**文件**：`agent/react_agent.py`

这是整个项目最核心的 ~100 行代码：

```python
import re
import json
from openai import OpenAI
from agent.tools import web_search, calculator, file_reader, TOOL_DESCRIPTIONS

# 工具注册表
TOOLS = {
    "web_search": web_search,
    "calculator": calculator,
    "file_reader": file_reader,
}

# ReAct Prompt 模板
REACT_SYSTEM_PROMPT = """你是一个智能助手，可以使用工具来完成用户的任务。

## 工作方式
你需要按照以下格式逐步思考和行动：

Thought: 分析用户的需求，决定下一步做什么。
Action: 要调用的工具名称。必须是 [{tool_names}] 之一。
Action Input: 传给工具的参数。
Observation: 工具返回的结果。

...（可重复 Thought/Action/Action Input/Observation 多次）

Thought: 我已经收集了足够的信息。可以给出最终答案了。
Final Answer: 对用户的最终回答。

## 规则
1. 每次只能调用一个工具
2. 先思考再行动，不要跳过 Thought
3. 如果工具返回的结果不够，可以再次调用
4. 如果任务需要用多个工具，依次调用
5. 如果遇到错误，尝试换一种方式解决
6. 最多调用 5 次工具，之后必须给出答案

{tool_descriptions}

当前时间：{current_time}
"""

class ReActAgent:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.max_iterations = 10

    def run(self, user_input: str) -> dict:
        """执行 ReAct 循环，返回最终答案和决策日志"""
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_input},
        ]
        
        decision_log = []  # 记录每一步决策（面试展示用）
        
        for i in range(self.max_iterations):
            # 1. 调用 LLM
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.1,  # 低温度保证决策稳定
            )
            reply = response.choices[0].message.content
            
            # 2. 解析 LLM 的输出
            action = self._parse_output(reply)
            decision_log.append({"iteration": i+1, "llm_output": reply, "parsed": action})
            
            # 3. 如果是最终答案，结束循环
            if action["type"] == "final_answer":
                return {
                    "answer": action["content"],
                    "iterations": i + 1,
                    "decision_log": decision_log,
                }
            
            # 4. 如果是工具调用，执行工具
            if action["type"] == "tool_call":
                tool_result = self._execute_tool(action["tool"], action["input"])
                
                # 5. 把工具结果追加到对话中
                messages.append({"role": "assistant", "content": reply})
                messages.append({
                    "role": "user",
                    "content": f"Observation: {tool_result}"
                })
        
        # 超出最大迭代次数，强制 LLM 给出答案
        messages.append({
            "role": "user",
            "content": "你已经达到了最大工具调用次数，请基于已有信息给出最终答案。"
        })
        final_response = self.client.chat.completions.create(
            model="deepseek-chat", messages=messages, temperature=0.1
        )
        return {
            "answer": final_response.choices[0].message.content,
            "iterations": self.max_iterations,
            "decision_log": decision_log,
            "note": "达到最大迭代次数，强制终止",
        }

    def _build_system_prompt(self) -> str:
        from datetime import datetime
        return REACT_SYSTEM_PROMPT.format(
            tool_names=", ".join(TOOLS.keys()),
            tool_descriptions=TOOL_DESCRIPTIONS,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

    def _parse_output(self, text: str) -> dict:
        """解析 LLM 输出中的 Action 和 Final Answer"""
        # 匹配 Final Answer
        final_match = re.search(r'Final Answer:\s*(.+)', text, re.DOTALL | re.IGNORECASE)
        if final_match:
            return {"type": "final_answer", "content": final_match.group(1).strip()}
        
        # 匹配 Action + Action Input
        action_match = re.search(r'Action:\s*(\w+)', text, re.IGNORECASE)
        input_match = re.search(r'Action Input:\s*(.+)', text, re.IGNORECASE)
        
        if action_match:
            tool = action_match.group(1).strip()
            tool_input = input_match.group(1).strip() if input_match else ""
            return {"type": "tool_call", "tool": tool, "input": tool_input}
        
        # 都匹配不到，当最终答案处理
        return {"type": "final_answer", "content": text.strip()}

    def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """执行工具并返回结果"""
        if tool_name not in TOOLS:
            return f"错误：未知工具 '{tool_name}'。可用工具: {list(TOOLS.keys())}"
        try:
            result = TOOLS[tool_name](tool_input)
            return str(result)
        except Exception as e:
            return f"工具执行失败: {e}"
```

**设计决策笔记**（面试用）：

> **为什么手写 ReAct 而不是用 LangChain 的 AgentExecutor？**
> 手写能精确控制每一步：Prompt 格式、解析逻辑、循环终止条件。我在调试时发现 LangChain 的默认解析器对中文场景兼容不好，自己写能任意定制。

> **temperature 为什么设 0.1？**
> Agent 的决策需要确定性——每次都选对工具比"有创造力"重要得多。0.1 基本是确定性输出，避免 Agent 在工具选择和参数上犯随机错误。

> **最大迭代次数为什么是 10？**
> 大多数任务 3-5 步完成。设 10 是加了安全余量——防止 LLM 陷入"调用→结果不满足→再调用→还不满足"的死循环。超过 10 次说明任务超出了 Agent 能力，应该终止并降级处理。

**单元测试**（`agent/test_agent.py`）：

```python
def test_simple_calculation():
    agent = ReActAgent(api_key="xxx")
    result = agent.run("1+1等于多少？")
    assert "2" in result["answer"]

def test_search_and_calculate():
    # 需要联网搜索的任务
    result = agent.run("深圳今天多少度？这个温度换算成华氏度是多少？")
    assert result["iterations"] >= 2  # 至少调用了两次工具

def test_no_tool_needed():
    # 不需要工具的问题，直接回答
    result = agent.run("你好，请介绍一下你自己")
    assert result["iterations"] == 1  # 一次工具都没调用
    assert len(result["answer"]) > 0

def test_file_read():
    # 先创建一个测试文件
    with open("test.txt", "w") as f:
        f.write("这是测试内容：苹果、香蕉、橙子")
    result = agent.run("读取 test.txt 并列出里面提到的水果")
    assert "苹果" in result["answer"]
```

**交付物**：
- [ ] `react_agent.py` 完成（~150 行）
- [ ] `tools.py` 完成（~60 行）
- [ ] 3 个测试用例通过
- [ ] CLI 脚本可交互：`python run_agent.py` 进入终端对话

---

### 2.4 CLI 交互界面（0.5 天）

**文件**：`agent/run_agent.py`

```python
from agent.react_agent import ReActAgent
from dotenv import load_dotenv
import os

load_dotenv()

agent = ReActAgent(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
)

print("=" * 50)
print("🤖 ReAct Agent 智能助手")
print("输入 'quit' 退出")
print("=" * 50)

while True:
    user_input = input("\n🧑 你: ")
    if user_input.lower() == 'quit':
        break

    print("🤔 Agent 思考中...")
    result = agent.run(user_input)

    print(f"\n🤖 Agent: {result['answer']}")
    print(f"\n--- 决策日志 ({result['iterations']} 步) ---")
    for step in result['decision_log']:
        print(f"  第{step['iteration']}步: {step['parsed']['type']}")
```

**交付物**：
- [ ] 终端对话可用，测试 5-10 个不同类型的问题

---

### 2.5 代码整理 + README（0.5 天）

**文件**：`agent/README.md`

```markdown
# ReAct Agent — 智能工具调用助手

基于 ReAct（Reasoning + Acting）范式的单 Agent 工具调用系统。

## 功能
- 自动判断用户需求，选择合适的工具
- 支持工具：联网搜索、数学计算、文件读取
- 完整的决策日志，可追溯每一步推理过程

## 技术栈
- Python + DeepSeek API
- 手写 ReAct 思考循环（Thought → Action → Observation → Final Answer）
- 最大 10 次迭代，自动防止死循环

## 快速开始
```bash
pip install openai duckduckgo-search python-dotenv
cp .env.example .env  # 填入 DEEPSEEK_API_KEY
python run_agent.py
```

## 示例
```
🧑 你: 帮我查一下今天的天气，然后算一下温度对应的华氏度
🤖 Agent: 今天天气晴，气温 35°C（对应 95°F）。
```
```

---

## 项目二时间分配

```
Day 1 (自习日) : 理解 ReAct 范式 + 看论文/blog
Day 2 (晚间)   : 实现 3 个工具函数
Day 3-4 (晚+自习): 实现 ReAct 循环（核心）
Day 5 (晚间)   : 写测试用例 + debug
Day 6 (晚间)   : CLI 交互界面 + 大量测试
Day 7 (自习日) : 整理代码 + README + 补课笔记
```

---

## 项目二结束验收

- [ ] `tools.py` — 3 个工具函数可用
- [ ] `react_agent.py` — ReAct 循环正确（Thought → Action → Observation → Final Answer）
- [ ] `run_agent.py` — CLI 可交互对话
- [ ] 至少 3 个测试用例通过
- [ ] 测试过 10 种不同类型的任务（纯计算、纯搜索、搜索+计算、文件读+总结、不需要工具...）
- [ ] 决策日志完整记录每一步
- [ ] README 完成

**完成后填写**：
- 实际完成日期：_____
- 用时：_____ 小时
- 最难的 bug：
- 面试可以讲的故事：
