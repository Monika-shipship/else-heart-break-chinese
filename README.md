# Else Heart.Break() 汉化文本润色工具

本项目提供了一套工具，用于半自动地对游戏《Else Heart.Break()》的汉化文本进行高质量润色。它利用 DeepSeek 的 API 来优化翻译文件（`.eng.mtf`）中右侧的文本，确保其格式为高质量、双语的“英文在前，中文在后”，同时保持左侧的瑞典语原文不变。

## 项目来源

本仓库是在 [1PercentSync/else-heart-break-chinese](https://github.com/1PercentSync/else-heart-break-chinese) 的基础上更新而来。感谢 `1PercentSync` 的初始工作！

## 核心功能

- **双语润色**: 将译文优化为“英文-中文”格式。
- **高并发处理**: 利用线程池并行处理多行或多批次文本，最大化效率。
- **成本控制**: 支持 `batch` 模式和动态背景 (`auto` 模式) 来节约 API 调用成本。
- **可追溯性**: 为每一次翻译尝试生成详细的 JSON 日志。
- **一致性引擎**: 通过“术语挖掘”和“术语表应用”两步工作流，确保专有名词的翻译统一。
- **强大的错误处理**: 包含 API 调用重试和批量任务失败自动降级为单行重试的机制。

## 安装与配置

1.  **安装依赖**:
    ```sh
    pip install requests regex
    ```
2.  **设置 API 密钥** (环境变量 `DEEPSEEK_API_KEY`):
    -   (PowerShell): `$env:DEEPSEEK_API_KEY="你的API密钥"`
    -   (Cmd): `set DEEPSEEK_API_KEY=你的API密钥`

## 使用方法

### 运行环境要求

**1. 确认当前目录**

**至关重要**: 所有命令都**必须**在项目的根目录（即 `else-heart-break-chinese` 文件夹）下执行。

**2. 使用 `-m` 模块化运行**

请始终使用 `python -m polish_tool.main` 的形式来运行，以避免导入错误。

### 用法示例与参数建议

#### 处理大型任务与分批运行

为安全起见，建议将大型任务分批执行。最方便的方法是使用 `--letters` 参数手动划分字母表：

- **第1批 (A-F):**
  ```sh
  python -m polish_tool.main --letters ABCDEF --mode batch
  ```
- **第2批 (G-L):**
  ```sh
  python -m polish_tool.main --letters GHIJKL --mode batch
  ```
- **后续批次以此类推...**

#### 参数设置建议 (经济性与效率)

- **追求最高性价比（推荐）**:
  ```sh
  python -m polish_tool.main --letters A --mode batch --group-size 16 --max-workers 32 --temperature 1.0
  ```
  - `--mode batch`: **必须**。节省成本的关键。
  - `--group-size 12-16`: **推荐**。平衡成本与稳定性的最佳范围。
  - `--max-workers 16-32`: **推荐**。可根据网络情况和API速率限制适当调整。
  - `--temperature 1.0`: **推荐**。最适合翻译和润色任务的温度。

- **追求最高质量 (处理核心剧情):**
  ```sh
  python -m polish_tool.main --only-files MainQuest.eng.mtf --mode batch --bg-mode full
  ```
  - `--bg-mode full`: 提供最完整的上下文，质量最高，但成本也最高。

#### 背景模式详解 (`--bg-mode`)

此参数用于平衡**翻译质量**和**API成本**。

- **`full` (完整模式)**: 发送全部三个背景文件 (`背景信息汇总.md`, `剧情与翻译参考详解.md`, `专有名词与翻译对照.md`)。质量最高，成本最高。
- **`lite` (精简模式)**: 仅发送 `专有名词与翻译对照.md`。成本最低。
- **`auto` (自动模式, 默认)**: 自动判断。如果文件名以 `_` 开头或包含 `phone`, `teach`, `siri`，则使用 `lite` 模式；否则使用 `full` 模式。

#### 术语表工作流详解 (`--mine-terms` 与 `--glossary-in`)

这两个功能是独立的，请按“先挖掘，后应用”的顺序操作。

**第一步：挖掘候选术语 (`--mine-terms`)**

此功能是“词频统计器”，用于发现潜在的专有名词。
1.  **运行**: `python -m polish_tool.main --letters ABC...Z_ --mine-terms`
2.  **得到输出**: 在 `glossary/out/.../` 目录下会生成 `glossary_candidates_...csv` 文件。
3.  **注意**: 这份文件是供您审阅的“原材料”，**不是可直接使用的三语对照表**。

**第二步：创建并应用术语表 (`--glossary-in`)**

1.  **人工审阅**: 打开 `glossary_candidates_...csv`，挑选出真正的专有名词。
2.  **创建术语表**: 新建一个您自己的 CSV 文件 (例如 `my_glossary.csv`) ，按 `source,target,tgt_lng` (瑞典语,英语,中文) 格式填入您希望强制统一的译法。
3.  **放置文件**: 将您创建的 `my_glossary.csv` 放入 `glossary/in/` 目录中。
4.  **应用**: 在后续的润色任务中，脚本会自动加载并应用此规则。

**总结：脚本不自动生成三语对照表。它通过 `--mine-terms` 提供候选词，由您来制作标准术语表，再通过 `--glossary-in` 在润色中应用。**

### 所有命令行参数

| 参数 | 默认值 | 描述 |
|---|---|---|
| `--src-dir` | `English` | 源文件目录。 |
| `--only-files` | `` | 仅处理这些文件（逗号分隔）。 |
| `--letters` | `` | 按文件首字母筛选。**不区分大小写，不支持范围(如A-G)**。 |
| `--max-workers` | `16` | 并行线程数。 |
| `--timeout` | `90` | HTTP 请求超时（秒）。 |
| `--temperature`| `1.0`| 采样温度。 |
| `--max-tokens`| `400`| 单行回复最大 tokens。 |
| `--mode` | `batch` | `line` (单行) 或 `batch` (批量)。 |
| `--group-size`| `12` | batch 模式的批大小。 |
| `--bg-mode` | `auto` | `full`, `lite`, 或 `auto`。 |
| `--dry-run` | `False` | 仅统计文件，不执行操作。 |
| `--log-dir` | `logs/deepseek` | 日志输出目录。 |
| `--progress-interval`| `5.0`| 进度更新间隔（秒）。 |
| `--glossary-in` | `glossary/in`| 术语表输入目录。 |
| `--glossary-out`| `glossary/out`| 术语表输出目录。 |
| `--mine-terms`| `False` | 启用术语挖掘。 |

---

## 如何使用翻译文件

本仓库的 `English` 目录包含了经过润色的、可直接在游戏中使用的翻译文件。所有文本均由 DeepSeek 翻译，并经过了初步校对。

**[点此下载翻译文件]()** (注：链接待补充)

### 使用方法

1.  **重要：备份原始文件！**
    请找到您的游戏安装目录，在其中定位到 `ElseHeartbreak_Data\InitData\Translations\English` 文件夹。**请先将这个 `English` 文件夹完整备份到其他安全位置**。

2.  **替换文件**
    将本仓库中的 `English` 文件夹**覆盖**游戏目录中原有的 `English` 文件夹。

3.  **进入游戏**
    启动游戏。如果进入后未显示中文，请尝试在游戏设置中切换一下语言（例如切换到其他语言再切回来）。

### 注意事项
- 本汉化为**英中对照**版本，以方便学习和校对。
- 由于游戏引擎的限制，过长的文本可能会在显示时被裁切。
