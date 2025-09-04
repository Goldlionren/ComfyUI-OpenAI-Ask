# OpenAI Ask (Vision/QA) – ComfyUI Custom Node

A ComfyUI custom node that calls **OpenAI-compatible APIs** (e.g., `llama.cpp`, `vLLM`, OpenWebUI proxies) to:
- **Reverse-prompt from an image** (Vision) and split **Prompt / Negative** automatically
- Act as a general **Q&A** node
- Output four channels: `positive`, `negative`, `answer_text`, `raw_json`

<p align="center">
  <img src="assets/5.png" width="900" alt="OpenAI Ask – ComfyUI custom node">
</p>

## ✨ Features

- **Vision input** with data URL (base64) for OpenAI Chat-style vision models  
- **Automatic Prompt/Negative split**  
  - Everything **before** `Prompt:` is dropped  
  - Negative supports multiple labels: `Negative`, `Negative Prompt`, `Neg`, `Avoid`, `Disallow`, `Do not`, `负向`, `负面`, `避免`, `不要`
- **Content source switch**: `content_only` (default), `auto`, `reasoning_only`
- Adjustable parameters: `temperature`, `top_p`, `max_tokens`, `max_side`, `image_format (JPEG/PNG)`, `jpeg_quality`
- **Custom API base** and endpoint (e.g., `http://192.168.1.242:10000/v1/chat/completions`)
- Clean outputs:  
  - `positive` → CLIP Text Encode `text`  
  - `negative` → CLIP Text Encode `text_negative`  
  - `answer_text` → full cleaned text (for view/debug)  
  - `raw_json` → original server response

---

## ✅ Tested backends

- **llama.cpp** (MiniCPM-V-4.5 GGUF + `--mmproj`, OpenAI-compatible server)  
- Should also work with **vLLM / OpenWebUI** or any OpenAI-style gateway (payload compatible)

---

## 📦 Installation

Clone into your ComfyUI `custom_nodes` folder and install requirements.

```bash
cd <ComfyUI>/custom_nodes
git clone https://github.com/Goldlionren/ComfyUI-OpenAI-Ask.git
pip install -r ComfyUI-OpenAI-Ask/requirements.txt
# Restart ComfyUI
```
---

# OpenAI Ask (Vision/QA) – ComfyUI Custom Node

通过 **OpenAI 兼容 API** 调用本地/私有 LLM，实现 **看图反推提示词 + 问答**：
- 自动输出 **Prompt / Negative** 两路文案（可直接接 CLIP）
- 支持自定义 API Base（例：`http://192.168.1.242:10000`）
- 兼容 **llama.cpp / vLLM / OpenWebUI** 等 OpenAI 风格服务
- 带图片压缩（最长边、JPEG/PNG、质量）与调参（temperature/top_p/max_tokens）

<p align="center">
  <img src="assets/screenshot-2.png" width="720"/>
</p>


## 📸 Screenshots

<p align="center">
  <img src="assets/5.png" width="900" alt="Code view – node core logic">
</p>

| ![Workflow – positive/negative outputs](assets/6.png) | ![GGUF models (MiniCPM-V-4.5)](assets/7.png) |
|---|---|
| ComfyUI 工作流与四路输出（positive / negative / answer_text / raw_json） | MiniCPM-V-4.5 GGUF 与 mmproj 文件示意 |

<p align="center">
  <img src="assets/screenshot-4.png" width="900" alt="MiniCPM-V repo – background info">
</p>



## ✨ 特性
- 正/负提示词**自动拆分**（会裁掉 `Prompt:` 之前所有内容）
- 负向标签**多写法兼容**：`Negative / Negative Prompt / Avoid / Disallow / Do not / 负向 / 避免 / 不要`
- 输出 4 路：`positive`、`negative`、`answer_text`、`raw_json`
- `content_source` 开关：`content_only / auto / reasoning_only`（默认只用 `content`，更干净）
- 图片以 data:URL 传输，局域网内低开销

## 🔧 安装
```bash
# 方式一（推荐）：clone 到 ComfyUI/custom_nodes 目录
cd <your-ComfyUI>/custom_nodes
git clone https://github.com/Goldlionren/ComfyUI-OpenAI-Ask.git

# 安装依赖（确保在 ComfyUI 使用的 Python 环境）
pip install -r ComfyUI-OpenAI-Ask/requirements.txt

# 重启 ComfyUI
```


