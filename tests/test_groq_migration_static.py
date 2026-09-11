"""Dependency-light regression checks for the Google -> Groq provider migration."""
from __future__ import annotations

import io
from pathlib import Path

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_provider_references_are_groq_only():
    forbidden = (
        "GOOGLE_API_KEY",
        "langchain_google_genai",
        "backend.tools.gemini_client",
        "has_google_api_key",
    )
    hits: list[str] = []
    for folder in ("backend", "frontend", "scripts", "tests"):
        for path in (ROOT / folder).rglob("*.py"):
            if path.name == Path(__file__).name:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(term in text for term in forbidden):
                hits.append(str(path.relative_to(ROOT)))
    assert not hits


def test_requirements_use_langchain_groq_not_google_genai():
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "langchain-groq==1.1.3" in text
    assert "langchain-google-genai" not in text


def test_env_example_is_placeholder_only_and_has_groq_models():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert 'GROQ_API_KEY="your-groq-api-key"' in text
    assert "GOOGLE_API_KEY" not in text
    assert 'CHAT_MODEL_NAME="qwen/qwen3.6-27b"' in text
    assert 'VISION_MODEL_NAME="qwen/qwen3.6-27b"' in text
    assert 'EMBEDDING_MODEL_NAME="all-MiniLM-L6-v2"' in text
    assert "MAX_PDF_PAGES=3" in text


def test_groq_key_pattern_is_in_secret_scanner():
    text = (ROOT / "scripts/preflight.py").read_text(encoding="utf-8")
    assert "gsk_" in text


def test_native_image_is_normalized_to_jpeg_for_groq_vision():
    from backend.tools.pdf_utils import ensure_vision_image_pages

    raw = (ROOT / "data/sample_images/sample_blood_test.png").read_bytes()
    pages = ensure_vision_image_pages(raw, max_pages=3)
    assert len(pages) == 1
    assert Image.open(io.BytesIO(pages[0])).format == "JPEG"


def test_pdf_vision_preprocessing_caps_request_at_three_images():
    from backend.tools.pdf_utils import ensure_vision_image_pages

    document = pymupdf.open()
    for index in range(5):
        page = document.new_page()
        page.insert_text((72, 72), f"Synthetic page {index + 1}")
    raw = document.tobytes()
    document.close()

    pages = ensure_vision_image_pages(raw, max_pages=5)
    assert len(pages) == 3
    assert all(Image.open(io.BytesIO(page)).format == "JPEG" for page in pages)
