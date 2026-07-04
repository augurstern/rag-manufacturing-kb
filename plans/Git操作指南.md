# Git 操作指南 —— 四仓库日常使用

## 四个仓库地址

| 项目 | 仓库地址 | 本地目录 |
|------|---------|---------|
| 项目一 RAG | `https://github.com/augurstern/rag-manufacturing-kb.git` | `C:\Users\31706\Desktop\简历RAG项目` |
| 项目二 Agent | `https://github.com/augurstern/react-agent-assistant.git` | 待创建 |
| 项目三 多Agent | `https://github.com/augurstern/multi-agent-research.git` | 待创建 |
| 项目四 LoRA | `https://github.com/augurstern/lora-finetune-manufacturing.git` | 待创建 |

---

## 一、仓库一（当前仓库）—— 已连接，可以直接 push

当前本地仓库 `C:\Users\31706\Desktop\简历RAG项目` 已经连上了远程 `origin`。

### 首次 push

```bash
cd "C:/Users/31706/Desktop/简历RAG项目"
git push -u origin main
```

> 如果 GitHub 仓库已有初始文件（README/LICENSE），第一次 push 会冲突。用 `git pull origin main --allow-unrelated-histories` 先拉再推。
> 推荐：GitHub 创建仓库时选"空仓库"（不要勾选 Add README），直接 push。

### 日常操作（每次写代码后执行）

```bash
# 1. 看当前改了哪些文件
git status

# 2. 添加要提交的文件
git add backend/app/services/parser.py    # 单个文件
# 或
git add backend/app/services/             # 整个目录
# 或
git add -A                                 # 所有改动（谨慎，先 git status 确认）

# 3. 提交（commit message 遵循规范）
git commit -m "[阶段X] 简短描述——具体做了什么"

# 4. 推送到 GitHub
git push

# 简写：第 2-4 步可以合成一条
git add backend/app/services/parser.py && git commit -m "[阶段二] 文档解析器——已完成PDF解析" && git push
```

### 标签操作（每个阶段结束时打）

```bash
# 打标签
git tag v0.1-env-ready
git tag -a v0.2-core-ready -m "核心RAG链路打通——检索准确率85%"

# 推送标签到 GitHub
git push --tags
# 或推送单个 tag
git push origin v0.1-env-ready

# 查看所有标签
git tag -l
```

---

## 二、仓库二/三/四 —— 到时候怎么创建

以仓库二为例（08.18 才需要做），仓库三和四操作完全一样：

```bash
# === 步骤 1：在 GitHub 网页上创建空仓库 ===
# 打开 https://github.com/augurstern
# 点击 New → 仓库名填 react-agent-assistant → 不要勾选任何初始化选项 → Create

# === 步骤 2：本地创建项目目录 ===
mkdir "C:/Users/31706/Desktop/react-agent-assistant"
cd "C:/Users/31706/Desktop/react-agent-assistant"

# === 步骤 3：初始化 Git ===
git init
git config user.name "开发者"        # 和仓库一保持一致
git config user.email "dev@example.com"

# === 步骤 4：连接远程仓库 ===
git remote add origin https://github.com/augurstern/react-agent-assistant.git

# === 步骤 5：创建第一个文件 + 首次提交 ===
echo "# ReAct Agent" > README.md
git add README.md
git commit -m "[初始化] 项目骨架——ReAct Agent智能工具调用助手"
git push -u origin main

# === 步骤 6：后续正常开发 ===
# 写代码 → git add → git commit → git push
```

---

## 三、分支策略

为了模拟真实工作经验，建议使用 feature 分支：

```bash
# 创建并切换到新分支
git checkout -b feat/parser           # 开发解析器
git checkout -b feat/chunker          # 开发分块器
git checkout -b feat/backend-api      # 开发后端API

# 在分支上开发...
git add ...
git commit -m "[阶段二] 文档解析器——支持PDF提取"  # 在 feat/parser 分支上提交

# 模块完成后，切回 main 并合并
git checkout main
git merge feat/parser

# 删除已完成的分支
git branch -d feat/parser

# 推送 main 到远程
git push
```

**分支命名规范**：
| 分支名 | 用途 |
|--------|------|
| `feat/parser` | 开发文档解析器 |
| `feat/chunker` | 开发分块策略 |
| `feat/backend-api` | 开发后端接口 |
| `feat/frontend-ui` | 开发前端页面 |
| `feat/docker-deploy` | Docker 部署配置 |
| `fix/xxx` | 修 bug |

**面试时的小加分**：GitHub 上有分支 + 合并记录，看起来像是真正的团队开发习惯。

---

## 四、commit message 规范

整个项目统一使用这套格式：

```
[阶段X] 简短标题——具体描述

示例：
[阶段二] 实现文档解析器——支持PDF/Word/TXT三种格式
[阶段二] 实现分块策略——滑动窗口(500/100)+父子分块+表格行分块
[阶段二] 修复分块重叠计算错误——chunk_overlap取值逻辑修正
[阶段三] FastAPI问答接口——支持流式SSE输出+来源引用返回
[阶段四] Docker Compose部署——backend+frontend+chromadb三服务编排
[阶段五] 架构设计文档——系统架构图+技术选型说明+模块设计细节
```

**原则**：
- 中文即可，不用勉强写英文
- 标题要让人一眼看懂做了什么
- 修复类 commit 写清楚修了什么问题
- 不要出现 `update`、`fix bug`、`修改` 这种无信息量的 message

---

## 五、一条龙操作流程

每次写代码的标准流程（按顺序来，不要跳步）：

```bash
# 1. 开始工作前，先拉最新代码（多人协作习惯，单人项目也做）
git pull

# 2. 创建分支（如果不确定改多少，先在分支上做）
git checkout -b feat/xxx

# 3. 写代码...写代码...写代码...

# 4. 随时看状态
git status
git diff                        # 看具体改了什么

# 5. 提交
git add <文件>
git commit -m "[阶段X] ..."

# 6. 如果分支上做了多个 commit，合并回 main
git checkout main
git merge feat/xxx
git branch -d feat/xxx

# 7. 推送
git push

# 8. 如果到了里程碑，打 tag
git tag -a v0.2-core-ready -m "核心RAG链路打通"
git push --tags
```

---

## 六、常见场景处理

### 场景 1：提交完了发现漏了文件

```bash
git add 漏掉的文件
git commit --amend --no-edit     # 追加到上一次 commit，不改 message
git push --force-with-lease      # 如果已经 push 过，需要强推
```

### 场景 2：commit message 写错了

```bash
git commit --amend -m "[阶段二] 修正后的message"
git push --force-with-lease
```

### 场景 3：改了一半想放弃，回到上次提交的状态

```bash
git checkout -- 文件名            # 放弃单个文件的改动
git reset --hard HEAD            # 放弃所有未提交的改动（危险！确认后再用）
```

### 场景 4：push 之前发现有不该提交的文件（如 .env）

```bash
# 如果还没 commit
git reset HEAD 不该提交的文件
# 如果已经 commit 了
git rm --cached 不该提交的文件    # 从 Git 追踪中移除，但保留本地文件
git commit -m "[阶段X] 移除误提交的.env文件"
git push
```

### 场景 5：在不同电脑上开发（家里笔记本 ↔ 公司电脑）

```bash
# 在第二台电脑上
git clone https://github.com/augurstern/rag-manufacturing-kb.git
cd rag-manufacturing-kb
cp .env.example .env  # 手动创建 .env（这个文件不在仓库里）
# 编辑 .env 填入 API Key

# 每次开始工作前
git pull

# 工作结束后
git push

# ⚠️ 注意：chroma_db/ 和 uploads/ 在 .gitignore 中，不会同步
# 所以向量库数据不会跨电脑同步，这是正常的
```

---

## 七、安全检查（每次 push 前必做）

```bash
# 1. 确认 .env 不在暂存区（绝对不能提交！）
git status | grep .env
# 应该只看到 .env.example，不应该有 .env

# 2. 搜索代码中是否有硬编码的 API Key
grep -r "sk-" --include="*.py" .  2>/dev/null
# 如果有输出，立即替换为环境变量读取方式

# 3. 确认 .gitignore 已包含敏感文件
cat .gitignore
# 应该有：.env、chroma_db/、uploads/、*.log

# 4. push 之前看一眼要推什么
git log origin/main..main --oneline
# 列出本地比远程多出来的 commit，确认无误再 push
```

---

## 八、每天的 Git 节奏

```
开始工作：
  1. cd 项目目录
  2. git pull                    （同步最新代码）
  3. git checkout -b feat/xxx    （开分支，小改动可跳过）

工作中：
  4. 写完一个小功能 → git add + git commit
  5. 写完一个模块 → git checkout main + git merge feat/xxx
  6. git push                    （推送到 GitHub）

结束工作：
  7. git status                  （确认没有遗留未提交的改动）
  8. git log --oneline -5        （看一下今天的提交记录）
```

---

## 九、仓库之间互不干扰

四个仓库是完全独立的，各自在各自的目录、各自的 Git 历史：

```
C:\Users\31706\Desktop\
├── 简历RAG项目/              ← 仓库一（已连接 origin）
├── react-agent-assistant/    ← 仓库二（08.18 创建）
├── multi-agent-research/     ← 仓库三（09.07 创建）
└── lora-finetune-manufacturing/ ← 仓库四（09.08 创建）
```

每个仓库独立 `git init`、独立 `git remote add`，互不影响。

---

## 十、常用命令速查表

| 想做什么 | 命令 |
|----------|------|
| 看改了什么 | `git status` |
| 看改的具体内容 | `git diff` |
| 加所有改动 | `git add -A` |
| 加指定文件 | `git add 路径/文件` |
| 提交 | `git commit -m "message"` |
| 推送 | `git push` |
| 拉取 | `git pull` |
| 看提交历史 | `git log --oneline -10` |
| 创建分支 | `git checkout -b 分支名` |
| 切换分支 | `git checkout 分支名` |
| 合并分支 | `git merge 分支名` |
| 删除分支 | `git branch -d 分支名` |
| 打标签 | `git tag -a v0.1 -m "说明"` |
| 推送标签 | `git push --tags` |
| 撤销未提交的改动 | `git checkout -- 文件名` |
| 看远程地址 | `git remote -v` |
| 修改上次 commit | `git commit --amend` |
