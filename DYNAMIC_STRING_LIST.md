# JR String to List (Dynamic) / 动态字符串列表

This node is bundled into **ComfyUI-OpenAI-Ask**. It does not require another custom-node package or a new Python dependency.

此节点直接集成到 ComfyUI-OpenAI-Ask 中，不需要额外安装其他第三方节点包，也不访问 OpenAI API。

## 使用方法 / Usage

1. Restart ComfyUI after upgrading the plugin. Search for **JR Node: String to List (Dynamic)** under **🥷 Integrations/OpenAI**.
2. Connect the first STRING output to `text_1`. When every input is connected, the node automatically adds an unused STRING port; use **+ Add STRING** to add one manually at any time.
3. Use **- Remove last unused** to delete only an unconnected trailing input (the first port is always preserved).
4. Connect the `list` output to the positive text input of **CLIP Text Encode** (or any downstream text encoder that supports ComfyUI's standard list mapping).
5. Queue once. ComfyUI normally evaluates the downstream text encoder and sampler once per STRING item. Output quantity depends on downstream batch/workflow configuration.

例如：5 个不同的 STRING → `text_1` 到 `text_5` → `list` → CLIP Text Encode `text` → KSampler。输出包含五个顺序独立的提示词项目，不是五段文本拼接成一个字符串。

## Important semantics / 执行语义

- The output socket type is **STRING**, with `OUTPUT_IS_LIST = (True,)`. This is the standard **ComfyUI execution list** convention, not a literal `LIST` socket type or a single comma/newline-separated string.
- The node declares `INPUT_IS_LIST = True` so it can concatenate upstream STRING execution lists without accidentally running itself repeatedly.
- Values are emitted in numeric port order (`text_1`, `text_2`, ... `text_10`), and order within any upstream list is preserved.
- Unconnected inputs are ignored. A deliberately connected empty STRING is retained as an item.
- Connecting a normal list to a node that implements `INPUT_IS_LIST = True` will make that node receive the list at once; downstream execution therefore depends on the target node.
- The original **OpenAI Ask (Vision/QA)** node and API behavior are unchanged.

## Quick tests / 简单测试

```bash
python -m unittest discover -s tests -p test_string_list.py -v
node tests/test_frontend.cjs # Optional: requires Node.js, no npm packages
```
