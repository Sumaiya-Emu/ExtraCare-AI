"""Multimodal Vision/OCR: extracts structured diagnostic or product data from images/PDFs."""
from __future__ import annotations

import base64

from langchain_core.messages import HumanMessage
from backend.config import settings
from backend.tools.groq_client import build_chat_model
from backend.core.json_extract import JSONExtractionError, extract_json_object
from backend.core.tracing import traceable
from backend.models.schemas import ExtractedLabData, ExtractedProductData
from backend.tools.pdf_utils import ensure_vision_image_pages, is_pdf, pdf_page_count

LAB_EXTRACTION_PROMPT = """You are a medical document extraction engine. Extract text only; do
not diagnose or infer findings that are not written on the document.

SUPPORTED DOCUMENTS:
1. Blood tests: CBC, metabolic, renal, liver, glucose/HbA1c, lipids, endocrine panels.
2. Urinalysis: dipstick, microscopy, protein, blood, glucose, ketones, leukocyte esterase,
   nitrite, RBC/WBC, casts, bacteria, specific gravity, pH, UACR/albumin-creatinine ratio.
3. WRITTEN radiology reports: X-Ray, Ultrasound, MRI, CT findings/impression text.

For radiology, extract the radiologist's written findings and impressions only. Do NOT interpret
raw DICOM films or infer abnormalities from an image of a scan.
For numeric laboratory measurements use `value`. For qualitative measurements such as Negative,
Trace, 1+, 2+, Few use `qualitative_value`. Never guess unreadable values.

If age, gender, or patient name are visibly printed, copy them exactly into the report-level fields.
Never infer them from reference ranges, names, or clinical values. For every laboratory item preserve
the visible raw value, any High/Low/Critical flag, and the page number when possible.

Respond with ONLY valid JSON, no prose or markdown fences:
{
  "document_type": "blood_panel|urinalysis|radiology_report|mixed|unknown",
  "reported_age": null,
  "reported_gender": "Male|Female" or null,
  "patient_name": null,
  "biomarkers": [
    {
      "name": "...",
      "value": null,
      "qualitative_value": null,
      "raw_value": null,
      "unit": null,
      "reference_range": null,
      "specimen": null,
      "report_flag": null,
      "source_page": null
    }
  ],
  "radiology_findings": [
    {
      "modality": "X-Ray|Ultrasound|MRI|CT|Other" or null,
      "body_part": null,
      "finding": "...",
      "impression": null,
      "abnormality": null,
      "source_page": null
    }
  ],
  "raw_text": "..."
}

If the upload is not a diagnostic/clinical document, return empty arrays and document_type
`unknown` rather than extracting product ingredients.
"""

PRODUCT_EXTRACTION_PROMPT = """You are a product-label OCR engine. Extract what is visibly printed
on packaged food, supplement, medicine, or skincare/cosmetic labels. Do not provide safety advice.
Do NOT treat medical lab values or radiology findings as product data.

Extract:
- product_name when visible
- product_type: food, supplement, medicine, skincare, cosmetic, or unknown
- exposure_route: oral, topical, or unknown based only on the visible product use/label
- each distinct ingredient/additive in printed order
- structured nutrition/quantity facts when visible (e.g. Sodium 780 mg per serving)
- allergen_statement when explicitly printed
- raw_text for auditability
Never guess unreadable text, quantities, product type, or allergens.

Respond with ONLY valid JSON, no prose or markdown fences:
{
  "product_name": null,
  "product_type": "food|supplement|medicine|skincare|cosmetic|unknown",
  "exposure_route": "oral|topical|unknown",
  "ingredients": ["..."],
  "nutrition_facts": [
    {"name": "Sodium", "value": 780, "unit": "mg", "per": "serving", "raw_value": "780 mg"}
  ],
  "allergen_statement": null,
  "raw_text": "..."
}
"""


class OCRExtractionError(RuntimeError):
    """Raised when the vision model output cannot be parsed as valid JSON."""


def _run_vision_extraction(input_bytes: bytes, prompt: str) -> tuple[dict, int, int]:
    if not settings.has_groq_api_key():
        raise OCRExtractionError("GROQ_API_KEY is not configured.")

    total_pages = pdf_page_count(input_bytes) if is_pdf(input_bytes) else 1
    pages = ensure_vision_image_pages(input_bytes, max_pages=settings.MAX_PDF_PAGES)
    model = build_chat_model(vision=True)

    content: list[dict] = [{"type": "text", "text": prompt}]
    for page_number, image_bytes in enumerate(pages, start=1):
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        content.append({"type": "text", "text": f"Document page {page_number}:"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"},
            }
        )

    response = model.invoke([HumanMessage(content=content)])
    try:
        return extract_json_object(response.content), len(pages), total_pages
    except JSONExtractionError as exc:
        raise OCRExtractionError(f"Vision model returned unparseable output: {exc}") from exc


@traceable("tool", name="ocr_tool.extract_lab_data", tags=["ocr", "document-extraction"])
def extract_lab_data(input_bytes: bytes) -> ExtractedLabData:
    payload, pages, total_pages = _run_vision_extraction(input_bytes, LAB_EXTRACTION_PROMPT)
    payload["pages_analyzed"] = pages
    payload["pages_total"] = total_pages
    payload["was_truncated"] = pages < total_pages
    return ExtractedLabData(**payload)


@traceable("tool", name="ocr_tool.extract_product_data", tags=["ocr", "product-extraction"])
def extract_product_data(input_bytes: bytes) -> ExtractedProductData:
    payload, pages, total_pages = _run_vision_extraction(input_bytes, PRODUCT_EXTRACTION_PROMPT)
    payload["pages_analyzed"] = pages
    payload["pages_total"] = total_pages
    payload["was_truncated"] = pages < total_pages
    return ExtractedProductData(**payload)
