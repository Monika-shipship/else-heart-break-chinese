# 批量润色翻译（Gemini/DeepSeek）

本仓库提供脚本 `polish_translations.py`，用于批量润色 `.mtf` 文件中的中文翻译，并输出到 `Chinese` 目录。

准备
- 安装依赖：`pip install requests`
- 准备 API Key（2 选 1）：
  - Gemini：设置环境变量 `GEMINI_API_KEY`
  - DeepSeek：设置环境变量 `DEEPSEEK_API_KEY`

快速开始
- 使用 Gemini：
  - PowerShell：`setx GEMINI_API_KEY "<your_api_key>"`
  - 运行：`python polish_translations.py --provider gemini --src-dir English --out-dir Chinese`
- 使用 DeepSeek：
  - PowerShell：`setx DEEPSEEK_API_KEY "<your_api_key>"`
  - 运行：`python polish_translations.py --provider deepseek --src-dir English --out-dir Chinese`

参数
- `--model` 指定模型（可选）：Gemini 默认 `gemini-1.5-flash-latest`；DeepSeek 默认 `deepseek-chat`
- `--batch-size` 每次请求翻译的条目数量，默认 20
- `--cache` 结果缓存/断点续跑 JSONL 文件，默认 `.polish_cache.jsonl`
- `--dry-run` 仅统计/生成输出文件，不实际调用接口

说明
- `.mtf` 行格式为：`"source" => "target"`，脚本仅替换 `target` 为润色后的中文，不改变 `source`
- 会尽量保留占位符 `%s`、`%d`、`{name}`、`{0}`、`<tag>`、`[link]` 等，不翻译代码片段
- 脚本会在 `Chinese` 目录下生成与 `English` 对应的文件

