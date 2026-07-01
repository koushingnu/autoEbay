"""英語タイトル/説明の生成サービス。

- OPENAI_API_KEY あり → OpenAI Chat Completions で英訳
- OPENAI_API_KEY なし → モック翻訳（APIを呼ばない）

TEST_MODE には依存しない。後から OPENAI_API_KEY を入れるだけで実翻訳へ切り替わる。
"""

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger("app.translate")

OPENAI_URL = "https://api.openai.com/v1/chat/completions"

_SYSTEM_PROMPT = (
    "You are a professional e-commerce copywriter for eBay listings. "
    "Translate the given Japanese product title and description into natural, "
    "concise English suitable for an eBay listing targeting international buyers. "
    "Keep brand names as-is. Return strictly JSON with keys 'title_en' and 'description_en'."
)


def _mock_translate(title: str, description: str) -> tuple[str, str]:
    title_en = f"[EN] {title} - Japan Import, Brand New"
    desc_en = (
        f"[EN] {description}\n\n"
        "This is a mock translation. Set OPENAI_API_KEY and TEST_MODE=false "
        "to generate a real English listing."
    )
    return title_en, desc_en


def _openai_translate(title: str, description: str) -> tuple[str, str]:
    payload = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"title": title, "description": description}, ensure_ascii=False
                ),
            },
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}

    with httpx.Client(timeout=60.0) as client:
        res = client.post(OPENAI_URL, json=payload, headers=headers)
    res.raise_for_status()

    content = res.json()["choices"][0]["message"]["content"]
    data = json.loads(content)
    return data.get("title_en", ""), data.get("description_en", "")


def translate(title: str, description: str) -> tuple[str, str, bool]:
    """(title_en, description_en, is_mock) を返す。"""
    if not settings.openai_api_key:
        logger.info("翻訳(モック): title=%s", title)
        t, d = _mock_translate(title, description)
        return t, d, True

    logger.info("翻訳(OpenAI): model=%s title=%s", settings.openai_model, title)
    t, d = _openai_translate(title, description)
    return t, d, False
