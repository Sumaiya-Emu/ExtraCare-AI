"""PDF handling for OCR and previews.

PDFs are rendered locally so the multimodal pipeline receives the same PNG input shape for images
and documents. OCR can analyze multiple PDF pages together; previews still show the first page.
"""
from __future__ import annotations

import io
from PIL import Image, ImageOps
import pymupdf

_PDF_MAGIC = b"%PDF"


def is_pdf(data: bytes) -> bool:
    return data[:4] == _PDF_MAGIC


def pdf_page_count(pdf_bytes: bytes) -> int:
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        return doc.page_count
    finally:
        doc.close()


def pdf_to_image_bytes(pdf_bytes: bytes, page_index: int = 0, zoom: float = 2.0) -> bytes:
    """Render one PDF page to PNG bytes."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        if doc.page_count == 0:
            raise ValueError("PDF has no pages.")
        page = doc.load_page(min(page_index, doc.page_count - 1))
        matrix = pymupdf.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        return pixmap.tobytes("png")
    finally:
        doc.close()


def pdf_to_image_pages(pdf_bytes: bytes, max_pages: int = 8, zoom: float = 2.0) -> list[bytes]:
    """Render up to ``max_pages`` pages to PNG for one multimodal OCR request."""
    if max_pages < 1:
        raise ValueError("max_pages must be at least 1.")
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        if doc.page_count == 0:
            raise ValueError("PDF has no pages.")
        count = min(doc.page_count, max_pages)
        matrix = pymupdf.Matrix(zoom, zoom)
        return [
            doc.load_page(i).get_pixmap(matrix=matrix, alpha=False).tobytes("png")
            for i in range(count)
        ]
    finally:
        doc.close()


def ensure_image_bytes(data: bytes) -> bytes:
    """Preview helper: pass through images unchanged, convert a PDF's first page."""
    if is_pdf(data):
        return pdf_to_image_bytes(data)
    return data


def ensure_image_pages(data: bytes, max_pages: int = 8) -> list[bytes]:
    """OCR helper: return one image or all permitted PDF pages."""
    if is_pdf(data):
        return pdf_to_image_pages(data, max_pages=max_pages)
    with Image.open(io.BytesIO(data)) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((2400, 2400))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return [buffer.getvalue()]


def _to_vision_jpeg(image: Image.Image, max_side: int = 1800, quality: int = 88) -> bytes:
    """Normalize one OCR page to a compact JPEG for Groq vision requests."""
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((max_side, max_side))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()


def ensure_vision_image_pages(data: bytes, max_pages: int = 3) -> list[bytes]:
    """Return compact JPEG pages for Groq vision.

    The configured Qwen vision model accepts a small number of images per request and
    Groq caps image-bearing requests at 20 MB. Rendering/normalizing locally keeps
    common phone photos and PDF pages comfortably below that ceiling.
    """
    max_pages = min(3, max(1, max_pages))
    if is_pdf(data):
        doc = pymupdf.open(stream=data, filetype="pdf")
        try:
            if doc.page_count == 0:
                raise ValueError("PDF has no pages.")
            pages: list[bytes] = []
            matrix = pymupdf.Matrix(1.7, 1.7)
            for i in range(min(doc.page_count, max_pages)):
                raw = doc.load_page(i).get_pixmap(matrix=matrix, alpha=False).tobytes("png")
                with Image.open(io.BytesIO(raw)) as image:
                    pages.append(_to_vision_jpeg(image))
            return pages
        finally:
            doc.close()
    with Image.open(io.BytesIO(data)) as image:
        return [_to_vision_jpeg(image)]
