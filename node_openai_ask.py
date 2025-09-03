# ComfyUI - OpenAI Ask (Vision/QA) Node for llama.cpp (MiniCPM-V 4.5)
# Outputs: positive, negative, answer_text, raw_json

import base64
import io
import json
import time
import re
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image


class OpenAIAskNode:
    """
    通过 OpenAI 兼容 API（llama.cpp/vLLM 等）进行问答/反推提示词。
    - 支持图片 -> OpenAI Chat Vision data:URL
    - 默认优先用 message.content（可选 content_source 切换为 auto/reasoning_only）
    - 自动拆分 Positive/Negative（正向裁掉 'Prompt:' 之前所有内容；负向兼容多种标签）
    - 另输出完整清洗后的文本与原始 JSON
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "question": ("STRING", {
                    "multiline": True,
                    "default": "Provide a detailed prompt based on this image. Output exactly two lines:\nPrompt: xxx\nNegative: xxx"
                }),
                "api_base": ("STRING", {
                    "default": "http://127.0.0.1:10000",
                    "tooltip": "llama.cpp server，例如：http://192.168.1.242:10000（末尾不要/）"
                }),
                "endpoint_path": ("STRING", {
                    "default": "/v1/chat/completions",
                    "tooltip": "llama.cpp 默认为 /v1/chat/completions"
                }),
                "model": ("STRING", {
                    "default": "minicpm-v-4.5",
                    "tooltip": "llama.cpp 通常忽略此字段，但OpenAI协议要求传；随意占位即可"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.3, "min": 0.0, "max": 2.0, "step": 0.05
                }),
                "top_p": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05
                }),
                "max_tokens": ("INT", {
                    "default": 512, "min": 1, "max": 8192, "step": 1
                }),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": (
                        "You are a vision-language assistant. "
                        "Return exactly TWO lines with no extra words:\n"
                        "Prompt: <positive>\nNegative: <negative>"
                    )
                }),
                "use_vision": (["auto", "force_on", "force_off"], {
                    "default": "auto",
                    "tooltip": "auto: 有图就带图；force_off: 纯文本；force_on: 即使没图也按Vision结构"
                }),
            },
            "optional": {
                # 选择从何处取文本
                "content_source": (["content_only", "auto", "reasoning_only"], {
                    "default": "content_only",
                    "tooltip": "content_only：只用 message.content；auto：content 优先否则 reasoning；reasoning_only：只用 reasoning_content"
                }),
                "image": ("IMAGE",),
                "api_key": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "llama.cpp 默认不校验，可留空"
                }),
                "extra_headers_json": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "额外HTTP头（JSON），如 {\"X-My-Header\":\"abc\"}"
                }),
                "timeout_sec": ("INT", {
                    "default": 60, "min": 1, "max": 600, "step": 1
                }),
                # 图像压缩相关
                "max_side": ("INT", {
                    "default": 1280, "min": 256, "max": 4096, "step": 16,
                    "tooltip": "最长边缩放到该值（等比）；0 表示不缩放"
                }),
                "image_format": (["JPEG", "PNG"], {
                    "default": "JPEG",
                    "tooltip": "建议JPEG以减小体积，加快本地传输"
                }),
                "jpeg_quality": ("INT", {
                    "default": 90, "min": 50, "max": 100, "step": 1,
                    "tooltip": "仅在JPEG时生效"
                }),
            },
        }

    # Four outputs:
    #   0: positive  1: negative  2: answer_text  3: raw_json
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "answer_text", "raw_json")
    FUNCTION = "ask"
    CATEGORY = "🥷 Integrations/OpenAI"

    # ====== 工具函数 ======
    @staticmethod
    def _resize_keep_aspect(pil: Image.Image, max_side: int) -> Image.Image:
        if max_side is None or max_side <= 0:
            return pil
        w, h = pil.size
        m = max(w, h)
        if m <= max_side:
            return pil
        scale = max_side / float(m)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        return pil.resize((new_w, new_h), Image.LANCZOS)

    @staticmethod
    def _image_to_data_url(image_tensor, max_side: int, fmt: str, jpeg_quality: int) -> Optional[str]:
        if image_tensor is None:
            return None
        try:
            import numpy as np
            if len(image_tensor.shape) != 4:
                return None
            img = image_tensor[0].cpu().numpy()  # HWC, float32 0..1
            img = (np.clip(img, 0.0, 1.0) * 255).astype("uint8")
            pil = Image.fromarray(img)
            pil = OpenAIAskNode._resize_keep_aspect(pil, max_side)
            buf = io.BytesIO()
            if fmt.upper() == "JPEG":
                pil = pil.convert("RGB")
                pil.save(buf, format="JPEG", quality=int(jpeg_quality), optimize=True)
                mime = "image/jpeg"
            else:
                pil.save(buf, format="PNG")
                mime = "image/png"
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return f"data:{mime};base64,{b64}"
        except Exception:
            return None

    @staticmethod
    def _build_messages(question: str, system_prompt: str, data_url: Optional[str], use_vision_mode: str):
        user_content: List[Dict[str, Any]] = []
        if question and question.strip():
            user_content.append({"type": "text", "text": question})
        if (use_vision_mode in ("auto", "force_on")) and data_url:
            user_content.append({"type": "image_url", "image_url": {"url": data_url}})
        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content if user_content else question})
        return messages

    @staticmethod
    def _merge_headers(api_key: str, extra_headers_json: str) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if extra_headers_json:
            try:
                extra = json.loads(extra_headers_json) or {}
                for k, v in extra.items():
                    headers[k] = v
            except Exception:
                pass
        return headers

    @staticmethod
    def _sanitize_reasoning_text(text: str) -> str:
        """去掉 '用户/User' 之类的开头杂项（不移除中间的 'Prompt:'，以免影响切分）"""
        if not isinstance(text, str):
            return ""
        t = text.replace("\r\n", "\n")
        t = re.sub(r'^\s*(用户|User)\s*[:：]?\s*\n?', '', t, flags=re.IGNORECASE)
        return t.strip()

    @staticmethod
    def _split_positive_negative(text: str) -> Tuple[str, str]:
        """
        规则：
        1) 若出现 “Prompt:”/“Positive:”/“提示词:”/“正向:” 等标签，
           则裁掉其 **之前** 的所有内容（包含标签本身），标签之后视为正向。
        2) 负向按以下标签切分（大小写不敏感）：
           Negative Prompt / Negative / Neg / Avoid / Disallow / Do not / 负向 / 负面 / 避免 / 不要
        3) 若未找到任何负向标签，则负向为空。
        """
        if not text:
            return "", ""

        s = text.replace("\r\n", "\n").strip()

        # 1) 裁掉 Prompt 之前所有内容
        prompt_label = re.search(r'(?is)(?:^|\n)\s*(prompt|positive|提示词|正向)\s*[:：]\s*', s)
        if prompt_label:
            s = s[prompt_label.end():].lstrip()

        # 2) 定位负向标签并切分
        neg_re = re.compile(
            r'(?im)\b('
            r'negative\s*prompt|negative|neg|'
            r'avoid|disallow|do\s*not|'
            r'负向|负面|避免|不要'
            r')\s*[:：]\s*'
        )
        m = neg_re.search(s)
        if m:
            pos = s[:m.start()].strip()
            neg = s[m.end():].strip()
        else:
            pos, neg = s.strip(), ""

        # 3) 再清一次残留标签
        pos = re.sub(r'(?im)^\s*(positive|prompt|提示词|正向)\s*[:：]\s*', '', pos).strip()
        neg = re.sub(
            r'(?im)^\s*(negative\s*prompt|negative|neg|avoid|disallow|do\s*not|负向|负面|避免|不要)\s*[:：]\s*',
            '',
            neg
        ).strip()

        return pos, neg

    @staticmethod
    def _extract_text_from_content(value: Any) -> str:
        """
        message.content 既可能是 string，也可能是 list[block]；
        这里尽量把里面的 text 抽取出来。
        """
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts: List[str] = []
            for blk in value:
                if isinstance(blk, dict):
                    # OpenAI 风格：{"type": "text", "text": "..."} 或 {"type":"output_text","text":"..."}
                    t = blk.get("text") or blk.get("content") or ""
                    if isinstance(t, str) and t.strip():
                        parts.append(t)
            return "\n".join(parts).strip()
        # 其他类型，尝试转字符串
        try:
            return str(value)
        except Exception:
            return ""

    # ====== 核心 ======
    def ask(self,
            question: str,
            api_base: str,
            endpoint_path: str,
            model: str,
            temperature: float,
            top_p: float,
            max_tokens: int,
            system_prompt: str,
            use_vision: str,
            content_source: str = "content_only",
            image=None,
            api_key: str = "",
            extra_headers_json: str = "",
            timeout_sec: int = 60,
            max_side: int = 1280,
            image_format: str = "JPEG",
            jpeg_quality: int = 90,
            ) -> Tuple[str, str, str, str]:

        # 1) 处理图片
        data_url = None
        if use_vision != "force_off":
            data_url = self._image_to_data_url(
                image_tensor=image,
                max_side=max_side,
                fmt=image_format,
                jpeg_quality=jpeg_quality
            )

        # 2) Headers
        headers = self._merge_headers(api_key, extra_headers_json)

        # 3) URL
        base = api_base.rstrip("/")
        path = endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"
        url = f"{base}{path}"

        # 4) Payload
        payload = {
            "model": model,
            "messages": self._build_messages(question, system_prompt, data_url, use_vision),
            "temperature": float(temperature),
            "top_p": float(top_p),
            "max_tokens": int(max_tokens),
            "stream": False
        }

        # 5) 请求
        t0 = time.time()
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout_sec)
        except Exception as e:
            err = f"[OpenAIAsk] request error: {e}"
            return ("", "", err, json.dumps({"error": err}, ensure_ascii=False, indent=2))

        elapsed = f"{(time.time() - t0):.2f}s"

        # 6) 解析
        positive = ""
        negative = ""
        answer_text = ""
        raw_json_text = ""
        try:
            data = resp.json()
            raw_json_text = json.dumps(data, ensure_ascii=False, indent=2)

            if resp.status_code >= 400:
                answer_text = f"[OpenAIAsk] HTTP {resp.status_code}: {data}"
            else:
                choices = data.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {}) or {}

                    content   = self._extract_text_from_content(msg.get("content"))
                    reasoning = self._extract_text_from_content(msg.get("reasoning_content"))
                    fallback  = self._extract_text_from_content(choices[0].get("text"))

                    # 先选源文本
                    if content_source == "content_only":
                        out_src = content if content else (fallback or reasoning)
                    elif content_source == "reasoning_only":
                        out_src = reasoning if reasoning else (fallback or content)
                    else:  # auto
                        out_src = content if content else (reasoning if reasoning else fallback)

                    # —— 拆分正/负：在原始 out_src 上做（避免先清洗把 'Prompt:' 删掉）——
                    positive, negative = self._split_positive_negative(out_src)

                    # —— 完整文本做一次轻度清洗（删掉开头“用户/User”等）——
                    answer_text = self._sanitize_reasoning_text(out_src)

                if not answer_text:
                    answer_text = "[OpenAIAsk] Empty content from server."

                answer_text += f"\n\n[latency: {elapsed}]"

        except Exception as e:
            answer_text = f"[OpenAIAsk] parse error: {e}\nHTTP {resp.status_code} Body: {resp.text}"
            raw_json_text = resp.text

        return (positive, negative, answer_text, raw_json_text)


NODE_CLASS_MAPPINGS = {
    "OpenAIAsk": OpenAIAskNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OpenAIAsk": "JR Node: OpenAI Ask (Vision/QA)",
}
