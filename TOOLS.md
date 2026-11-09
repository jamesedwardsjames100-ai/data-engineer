# TOOLS.md - 工具与软件使用清单

> 请列出本次笔试中**所有使用过的软件、工具、库**。
> 
> 📌 **填写要求**：
> - 每个工具至少写明三件事：解决什么问题、使用场景、替代方案
> - 不要为了凑数列出 `os`、`sys` 这种标准库
> - 重点列那些**对你解题有实质帮助**的工具
> - 不熟悉的工具不要硬列 —— 面试会追问

---

## 🤖 AI 工具

### 工具 1：Cursor 

- **版本/型号**：内置 Claude 3.5 Sonnet / GPT-4o / DeepSeek API
- **解决了什么问题**：作为主力开发环境，极大地提升了样板代码（如 `logging` 配置、`merge_asof` 模板、API 请求体封装）的编写效率。
- **使用场景**：整个项目的 Python 脚本编写；遇到环境报错时，直接选中报错栈让 AI 解释。
- **替代方案**：VS Code + GitHub Copilot 插件。


### 工具 2：deep seek

- **版本/型号**：DeepSeek-V3 / R1
- **解决了什么问题**：在 Cursor 免费额度耗尽时作为强力替补。主要用于生成大段复杂的 SQL 查询（如 Q2.3 的窗口函数）以及设计 Q4 的英文 Few-shot Prompt 模板。
- **使用场景**：Q2 和 Q4 模块的核心逻辑设计。
- **替代方案**：Gemini、ChatGPT 网页版。

---

## 💻 IDE / 开发环境

### 工具 1：Cursor

- **解决了什么问题**：内置 AI 助手，支持自然语言直接修改多行代码。
- **使用场景**：全项目开发与调试。
- **替代方案**：PyCharm 专业版

---

## 🐍 Python 库

### 数据处理
| 库 | 版本 | 用途 | 替代方案 |
|----|------|------|----------|
| pandas | 2.2.x | 核心 ETL 处理、数据清洗、RFM 聚合计算 | Polars |
| numpy | 1.26.x | 辅助 Pandas 进行数值计算、固定随机种子 | 无 |
| pyarrow | 15.x | 支持 Q3 的 ETL 结果保存为 `.parquet` 列式存储格式 | fastparquet |

### 数据库 / SQL（强制使用 MySQL 8.0+）

| 库 | 版本 | 用途 | 替代方案 |
|----|------|------|----------|
| pymysql | 1.1.x | 纯 Python 实现的 MySQL 驱动 | mysqlclient（需 C 编译） |
| sqlalchemy | 2.0.x | ORM 框架，用于 Q2 中利用 `to_sql` 将 Olist CSV 高效批量灌入 MySQL | 直接用 `pymysql` 执行原生 SQL 插入 |
| cryptography | 42.0+ | 解决 MySQL 8.0 默认 `caching_sha2_password` 认证导致的报错 | 修改 MySQL 用户认证模式为 `mysql_native_password` |

### LLM / API

| 库 | 版本 | 用途 | 替代方案 |
|----|------|------|----------|
| requests | 2.31.x | 直接向 DeepSeek 发送原生 HTTP POST 请求，绕过 SDK 版本冲突 | `openai` SDK（遇到 Python 3.13 冲突报错，故放弃） |
| tenacity | 8.2.x | 为 Q4 的 API 调用提供带指数退避的高可用重试机制 | 手写 `while` 循环 `try-except` |
| python-dotenv | 1.0.x | 从 `.env` 文件中安全读取 API Key，防止密钥泄露到 Git 仓库 | 直接在代码中硬编码（不安全） |

### 其他

| 库 | 版本 | 用途 | 替代方案 |
|----|------|------|----------|
| kagglehub | 0.2.x | 官方提供的一键下载 Kaggle 数据集的库 | Kaggle CLI 命令行 |
| tracemalloc | 内置 | Q3 中用于监控 ETL Pipeline 运行时的内存峰值 | memory_profiler |



---

## 🛠️ 数据库工具

### 工具 1：MySQL Workbench 8.0

- **解决了什么问题**：可视化连接 MySQL 数据库，执行 Q2 的复杂 SQL 查询。
- **使用场景**：验证 CTE、窗口函数是否报错；执行 `EXPLAIN` 语句对比慢查询优化前后的执行计划（扫描行数、type 变化）。
- **替代方案**：DBeaver、DataGrip。

---

## 🔍 调试与分析工具

> 比如 line_profiler、memory_profiler、pytest 等

**Python Debug (print/Logging)**：利用 `logging` 模块将日志同时输出到控制台和文件，在 Q3 和 Q4 中精准定位是哪条测试数据引发了报错。
- **`tracemalloc`**：在 Q3 ETL 结束时，精准捕获 100 万行数据处理的内存峰值，防止 OOM。

---

## 🌐 在线资源 / 文档

> 不需要列出每一次搜索，只列那些对你帮助最大的资源

例如：
- **Pandas 官方文档**：用于查 `merge_asof` 的精确用法（Q3.1 退货匹配）
- **MySQL 8.0 Reference Manual**：窗口函数、JSON 函数、执行计划（EXPLAIN ANALYZE）的精确语义
- **某篇博客**：（如果你参考了具体的博客，请贴链接）


1、**Pandas 官方文档**：重点查阅了 `merge_asof` 的参数（`direction`、`by`）以及底层类型冲突的解决方案。
2. **MySQL 8.0 Reference Manual**：查阅了 `EXPLAIN` 执行计划的 Type 含义、窗口函数（`RANK() OVER`）的精确用法。
3. **DeepSeek 开放平台文档**：查阅了 JSON Output 的格式要求以及 API 请求结构。
---

## 📌 关键工具决策反思

> 这部分是给我们看你对工具的理解深度的

### 你做过的最重要的工具选型决策是？为什么？

例如："Q2 强制 MySQL，我在 Q2.4 优化题里对 `orders.order_purchase_timestamp` 加了组合索引并把 `LOWER(c.customer_city) LIKE '%sao%'` 改写成不依赖函数的形式，把执行时间从 X 秒降到 Y 秒"

**放弃 `openai` SDK，改用原生 `requests` 库请求 DeepSeek API。**
在 Q4 模块中，我最初使用了 `openai` 官方库，但本地 Python 3.13 环境报出了底层的 `TypeError`。我排查后发现是第三方库的依赖冲突。为了不陷入无尽的修复环境泥潭，我果断决定**剥离 SDK 的封装，直接用最原生的 `requests.post` 构造 JSON 请求体**。这让我不仅完美绕过了报错，还顺带用 `tenacity` 实现了极其轻量的重试机制，彻底掌握了请求的底层控制权。


### 你尝试过但**放弃**的工具/方案？

> 这能体现你的判断力

**放弃 `iterrows` 与 `apply` 循环全表。**
在 Q3 ETL 中，AI 第一版给出的退货匹配代码使用了 `iterrows` 循环，这对于 100 万行数据是性能灾难。我通过查阅文档，改用了基于 C 语言底层的 `merge_asof` 二分查找，将耗时从可能的几十分钟压缩到了 1.87 秒。
### 如果再做一次，你会换用什么工具？

1. **Pandas 换成 Polars**：如果面对千万级数据，我会尝试用 Polars 替代 Pandas，其基于 Rust 的底层实现能提供更好的内存控制和并行处理能力。
2. **本地环境改用 Docker**：为了彻底解决 MySQL 8.0 的本地安装和认证问题，我会直接写一个 `docker-compose.yml`，一键拉起 MySQL 和 Redis，环境隔离会更干净。
