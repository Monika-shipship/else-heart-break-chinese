# Else Heart.Break() 汉化文本润色工具

本项目提供了一套工具，用于半自动地对游戏《Else Heart.Break()》的汉化文本进行高质量润色。它利用 DeepSeek 的 API 来优化翻译文件（`.eng.mtf`）中右侧的文本，确保其格式为高质量、双语的“英文在前，中文在后”，同时保持左侧的瑞典语原文不变。

该工具为高并发、成本可控、可追溯和一致性而设计。

## 项目来源

本仓库是在 [1PercentSync/else-heart-break-chinese](https://github.com/1PercentSync/else-heart-break-chinese) 的基础上更新而来。

感谢 `1PercentSync` 的初始工作！

## 核心功能

- **双语润色**: 将译文优化为“英文-中文”格式。
- **高并发处理**: 利用线程池并行处理多行或多批次文本，最大化效率。
- **成本控制**:
    - 支持 `batch`（批量）模式，以分摊单次 API 调用的系统开销。
    - 具有 `auto`（自动）背景模式，能为 UI/系统类文本发送更轻量的上下文，以节省 token。
    - 充分利用 DeepSeek 的提示缓存机制，在处理重复性高的文件时能显著降低成本。
- **可追溯性**: 为每一次翻译尝试生成详细的 JSON 日志，内容包括完整的提示、API 原始响应、最终输出及任何错误信息。
- **一致性引擎**:
    - **输入术语表**: 使用用户提供的 CSV 术语表，对在原文中匹配到的术语强制使用给定的译法。
    - **术语挖掘**: 自动从游戏文件中发现候选术语（单词和短语），并将其输出为 CSV 文件供人工审核。这有助于迭代式地构建和扩充术语表。
    - **规范化规则**: 在最终写入文本前，应用一套可配置的正则表达式规则来统一术语和风格（例如，自动将“锐舞派对”替换为“狂欢派对”）。
- **强大的错误处理**: 包含 API 调用重试机制，以及在批量处理失败时自动降级为单行模式重试，以最大化成功率。

## 项目结构

项目代码经过重构，形成了模块化的结构，以提高可维护性和清晰度。

```
.
├── English/                  # 存放 .mtf 源文件的目录
├── glossary/
│   ├── in/                   # 在此放入输入术语表 (例如 terms.csv)
│   └── out/                  # 挖掘出的候选术语将输出到此目录
├── logs/
│   └── deepseek/             # 详细的运行日志将按时间戳保存在这里
├── tools/
│   └── canonical_rules.json  # (可选) 自定义术语规范化规则
├── polish_tool/              # 工具的核心 Python 包
│   ├── __init__.py
│   ├── api_client.py         # 封装所有与 DeepSeek API 的通信
│   ├── config.py             # 存放默认配置，如规范化规则
│   ├── file_io.py            # 负责读写 .mtf 特定文件格式
│   ├── glossary_tool.py      # 管理输入术语表和术语挖掘功能
│   ├── main.py               # ✨ 主入口脚本
│   ├── prompts.py            # 构造发送给大模型的 System 和 User 提示
│   ├── runner.py             # 负责处理单个文件的核心引擎
│   ├── text_processing.py    # 用于清洗、校验和规范化文本的函数
│   └── utils.py              # 通用辅助函数（日志、格式化等）
├── polish_translations.py    # (旧入口) 仅供参考，请勿直接运行
└── README.md                 # 本文档
```

## 安装与配置

1.  **安装依赖**: 本工具需要 `requests` 和 `regex` 库。
    ```sh
    pip install requests regex
    ```

2.  **设置 API 密钥**: 脚本需要一个 DeepSeek API 密钥。请将其设置为环境变量 `DEEPSEEK_API_KEY`。

    -   **Windows (Command Prompt)**:
        ```cmd
        set DEEPSEEK_API_KEY=你的API密钥
        ```
    -   **Windows (PowerShell)**:
        ```powershell
        $env:DEEPSEEK_API_KEY="你的API密钥"
        ```
    -   **Linux/macOS**:
        ```sh
        export DEEPSEEK_API_KEY='你的API密钥'
        ```

## 使用方法

### 运行环境要求

**1. 确认当前目录**

**至关重要**: 所有命令都**必须**在项目的根目录（即 `else-heart-break-chinese` 文件夹）下执行。

```powershell
# 正确的目录
PS D:\Repos\Game\else-heart-break-chinese>

# 错误的目录 (会导致 ModuleNotFoundError)
PS D:\Repos\Game\else-heart-break-chinese\polish_tool>
```

如果您不确定当前位置，可以先 `cd` 到项目根目录。

**2. 使用 `-m` 模块化运行**

请始终使用 `python -m polish_tool.main` 的形式来运行，而不是 `python polish_tool/main.py`。这能确保 Python 正确地将 `polish_tool` 作为一个包来加载，避免导入错误。

### 用法示例与参数建议

#### 基础示例

**1. 处理单个文件 (推荐用于测试):**
```sh
python -m polish_tool.main --only-files Araki_AfterGhostVisit.eng.mtf --mode batch --group-size 16 --max-workers 32 --bg-mode auto
```

**2. 处理所有以特定字母开头的文件:**
```sh
# 处理 'A' 开头的文件
python -m polish_tool.main --letters A --mode batch

# 处理 '_' 开头的文件 (系统文本，建议使用 full 模式)
python -m polish_tool.main --letters _ --mode batch --bg-mode full
```

**3. 使用术语表并开启术语挖掘:**
```sh
python -m polish_tool.main --letters B --glossary-in glossary/in --mine-terms --glossary-out glossary/out
```
-   **输入**: 运行前，在 `glossary/in` 目录中放入一个或多个 CSV 文件。CSV 文件必须包含 `source,target,tgt_lng` 这三列（分别对应瑞典语、英语、中文）。
-   **输出**: 脚本会在 `glossary/out` 内一个以时间戳命名的子目录中，生成一个 `glossary_candidates_*.csv` 文件。

**4. 运行一个即将开始的润色任务:**
这个例子展示了在开启术语挖掘的同时，对一个较大的对话文件进行处理的典型命令。
```sh
python -m polish_tool.main --only-files Amanda_ClubDotGig2.eng.mtf --mode batch --group-size 16 --max-workers 32 --bg-mode auto --temperature 1.0 --progress-interval 3 --progress-every 8 --mine-terms
```

**5. 试运行 (Dry Run):**
如果您想查看哪些文件将被处理，但不想实际调用 API 或写入文件，请使用 `--dry-run` 标志。
```sh
python -m polish_tool.main --letters C --dry-run
```

#### 参数设置建议 (经济性与效率)

为了在**成本**、**速度**和**质量**之间取得平衡，我们推荐以下参数组合作为参考：

- **追求最高性价比（推荐）**:
  ```sh
  python -m polish_tool.main --letters A --mode batch --group-size 16 --max-workers 32 --temperature 1.0
  ```
  - `--mode batch`: **必须使用**。批量模式是节省成本的关键，它将多行文本打包在一次 API 调用中，从而分摊了 `system_prompt` 带来的固定开销。
  - `--group-size 12-16`: **推荐值**。这个范围在分摊成本和保持提示词大小之间取得了良好平衡。太小的组（如 4-8）节省成本效果不明显；太大的组（如 32+）可能导致 API 超时或模型在处理长上下文时表现下降。
  - `--max-workers 16-32`: **推荐值**。这个数值决定了同时有多少个“批次”在进行处理。它主要受您的网络环境和 API 账户的速率限制影响。如果您的网络状况良好且未遇到速率限制错误，可以适当调高此值（如 `48` 或 `64`）以追求极致速度。如果频繁出现网络错误，应降低此值。
  - `--temperature 1.0`: **推荐值**。对于翻译和润色任务，`1.0` 是一个稳定且能产出高质量、一致性较好结果的温度。过高的温度（如 `1.5`）可能导致输出不稳定、胡言乱语；过低的温度（如 `0.7`）则可能让译文显得僵硬、缺乏活力。

- **追求最高质量 (例如处理核心剧情或UI文本):**
  ```sh
  python -m polish_tool.main --only-files MainQuest.eng.mtf --mode batch --group-size 12 --max-workers 16 --bg-mode full --temperature 1.0
  ```
  - `--bg-mode full`: **核心区别**。使用 `full` 模式会向模型提供最完整的背景信息，有助于其做出最符合上下文的判断，但成本也最高。此模式非常适合处理关键的剧情文件或需要高度一致性的系统UI文本。
  - `--group-size` 和 `--max-workers` 可以适当调低，因为 `full` 模式的请求本身较大，降低并发数有助于提高稳定性。

- **最快速地验证单个文件的效果:**
  ```sh
  python -m polish_tool.main --only-files YourFile.eng.mtf --mode line --max-workers 48
  ```
  - `--mode line`: 单行模式虽然成本高，但每个请求都非常快，且完全独立，适合快速检查少量文本的润色效果。

#### 背景模式详解 (`--bg-mode`)

`--bg-mode` 参数是平衡**翻译质量**和**API成本**的关键。它决定了每次向 AI 发送请求时，要提供多少背景信息。

背景信息来源于 `背景信息/` 目录下的三个文件：
- `背景信息汇总.md` (世界观、阵营、主要人物等)
- `剧情与翻译参考详解.md` (详细的剧情流程和对话分析)
- `专有名词与翻译对照.md` (最核心的术语、地点、物品列表)

不同模式的含义如下：

- **`--bg-mode full` (完整模式)**
  - **发送内容**: 固定规则 + **全部三个背景文件**。
  - **优点**: 为 AI 提供最全面的上下文，有助于它理解深层剧情和人物语气，**翻译质量最高**。
  - **缺点**: 输入 token 数量最多，**成本最高**。
  - **适用场景**: 处理核心主线剧情、人物重要对话，或任何需要高度情景一致性的文件。

- **`--bg-mode lite` (精简模式)**
  - **发送内容**: 固定规则 + **仅 `专有名词与翻译对照.md`**。
  - **优点**: 输入 token 数量最少，**成本最低**。
  - **缺点**: 缺少剧情和世界观背景，AI 可能无法准确把握对话的深层含义。
  - **适用场景**: 处理通用文本、系统菜单、UI界面、教学提示等与核心剧情关联较小的文件。

- **`--bg-mode auto` (自动模式，默认)**
  - **判断逻辑**: 这是一个智能启发式策略。脚本会检查当前处理的文件名：
    - 如果文件名以 `_` 开头，或包含 `phone`、`teach`、`siri` 等关键字，则**自动使用 `lite` 模式**。
    - 否则，**自动使用 `full` 模式**。
  - **设计思路**: 系统菜单/UI (`_`开头) 和电话/教学等文件，其内容通常独立于主线剧情，使用 `lite` 模式可在保证基本准确性的前提下大幅节约成本。而其他大部分文件（如角色对话）则使用 `full` 模式以保证质量。

### 所有命令行参数

| 参数                  | 默认值           | 描述                                                                     |
| --------------------- | ---------------- | ------------------------------------------------------------------------ |
| `--src-dir`           | `English`        | 包含 `.mtf` 源文件的目录。                                               |
| `--only-files`        | ``               | 用逗号分隔的待处理文件名列表。                                           |
| `--letters`           | ``               | 按文件首字母筛选 (例如, `A_` 会处理 A 和 _ 开头的文件)。                 |
| `--max-workers`       | `16`             | 并行 API 请求的线程数。                                                  |
| `--timeout`           | `90`             | HTTP 请求超时时间（秒）。                                                |
| `--temperature`       | `1.0`            | LLM 采样温度，推荐 `1.0` 以获得稳定结果。                                |
| `--max-tokens`        | `400`            | 单行模式下 API 回复的最大 token 数。                                     |
| `--mode`              | `batch`          | `line` (每行一次API调用) 或 `batch` (每批一次调用)。                     |
| `--group-size`        | `12`             | `batch` 模式下每批处理的行数。                                           |
| `--bg-mode`           | `auto`           | `full` (发送全部背景), `lite` (发送精简背景), 或 `auto` (自动判断)。   |
| `--dry-run`           | `False`          | 若设置，则仅列出待处理文件并退出。                                       |
| `--log-dir`           | `logs/deepseek`  | 存放详细 JSON 行日志的目录。                                             |
| `--progress-interval` | `5.0`            | 在控制台打印进度更新的间隔时间（秒）。                                   |
| `--glossary-in`       | `glossary/in`    | 用户自定义术语表 CSV 文件的输入目录。                                    |
| `--glossary-out`      | `glossary/out`   | 挖掘出的候选术语 CSV 文件的输出目录。                                    |
| `--mine-terms`        | `False`          | 若设置，则启用自动术语挖掘功能。                                         |

---

## 如何使用翻译文件

本仓库的 `English` 目录包含了经过润色的、可直接在游戏中使用的翻译文件。所有文本均由 DeepSeek 翻译，并经过了初步校对。

**[点此下载翻译文件]()** (注：链接待补充)

### 使用方法

1.  **重要：备份原始文件！**
    请找到您的游戏安装目录，在其中定位到 `ElseHeartbreak_Data\InitData\Translations\English` 文件夹。**请先将这个 `English` 文件夹完整备份到其他安全位置**（直接在原地复制粘贴进行备份可能导致问题）。

2.  **替换文件**
    将本仓库中的 `English` 文件夹**覆盖**游戏目录中原有的 `English` 文件夹。

3.  **进入游戏**
    启动游戏。如果进入后未显示中文，请尝试在游戏设置中切换一下语言（例如切换到其他语言再切回来），这通常可以解决问题。

### 注意事项
- 本汉化为**英中对照**版本，以方便学习和校对。
- 由于游戏引擎的限制，过长的文本可能会在显示时被裁切。