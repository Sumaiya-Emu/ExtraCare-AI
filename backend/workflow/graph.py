"""LangGraph: router -> specialist -> confidence gate -> risk -> arbiter."""
from __future__ import annotations

from typing import Optional, TypedDict

from langgraph.graph import END, StateGraph

from backend.agents.arbiter_agent import synthesize
from backend.agents.cross_match_agent import analyze_cross_match
from backend.agents.lab_agent import analyze_lab
from backend.agents.product_agent import analyze_product
from backend.agents.router_agent import route
from backend.agents.text_check_agent import analyze_text_ingredients
from backend.core.confidence import assess_lab_confidence, assess_product_confidence, assess_text_confidence
from backend.core.errors import AnalysisUnavailableError
from backend.core.risk_engine import calculate_hazard_score
from backend.core.safety.clinical_attention import assess_underlying_clinical_attention
from backend.core.safety.input_guard import validate_expected_product_type, validate_profile_consistency
from backend.models.schemas import (
    AnalysisConfidence,
    AnalysisResult,
    ExtractedLabData,
    ExtractedProductData,
    PatientProfile,
    PipelineOutput,
    RiskReport,
)
from backend.tools.ocr_tool import OCRExtractionError
from backend.core.tracing import traceable


class GraphState(TypedDict, total=False):
    mode: str
    profile: PatientProfile
    image_bytes: Optional[bytes]
    product_image_bytes: Optional[bytes]
    ingredients_text: Optional[str]
    fast_mode: bool
    expected_product_type: Optional[str]
    warnings: list[str]
    underlying_clinical_attention: str
    extracted_summary: str
    extracted_lab: ExtractedLabData
    extracted_product: ExtractedProductData
    analysis: AnalysisResult
    confidence: AnalysisConfidence
    score: int
    verdict: str
    color: str
    report: RiskReport


def _router_node(state: GraphState) -> GraphState:
    return {"mode": route(state["mode"], state["profile"])}


def _lab_node(state: GraphState) -> GraphState:
    extracted, analysis = analyze_lab(state["image_bytes"], state["profile"])
    biomarker_names = ", ".join(b.name for b in extracted.biomarkers)
    radiology_names = ", ".join(f.finding for f in extracted.radiology_findings)
    summary = ", ".join(t for t in [extracted.document_type.replace("_", " "), biomarker_names, radiology_names] if t)
    return {
        "extracted_summary": summary,
        "extracted_lab": extracted,
        "analysis": analysis,
        "confidence": assess_lab_confidence(extracted),
        "warnings": validate_profile_consistency(extracted, state["profile"]),
        "underlying_clinical_attention": assess_underlying_clinical_attention(extracted),
    }


def _product_node(state: GraphState) -> GraphState:
    extracted, analysis = analyze_product(state["image_bytes"], state["profile"], use_live_search=not state.get("fast_mode", False))
    summary_parts = [extracted.product_name or "", ", ".join(extracted.ingredients)]
    return {
        "extracted_summary": " | ".join(p for p in summary_parts if p),
        "extracted_product": extracted,
        "analysis": analysis,
        "confidence": assess_product_confidence(extracted),
    }


def _cross_match_node(state: GraphState) -> GraphState:
    lab_data, product_data, analysis = analyze_cross_match(
        state["image_bytes"],
        state["product_image_bytes"],
        state["profile"],
        expected_product_type=state.get("expected_product_type"),
    )
    lab_conf = assess_lab_confidence(lab_data)
    product_conf = assess_product_confidence(product_data)
    score = min(lab_conf.score, product_conf.score)
    reasons = [f"Lab: {r}" for r in lab_conf.reasons] + [f"Product: {r}" for r in product_conf.reasons]
    confidence = AnalysisConfidence(
        level="low" if score < 50 else "medium" if score < 80 else "high",
        score=score,
        reasons=reasons,
        can_show_verdict=score >= 50,
    )
    biomarker_names = ", ".join(b.name for b in lab_data.biomarkers)
    ingredient_names = ", ".join(product_data.ingredients)
    summary = f"Lab ({lab_data.document_type.replace('_', ' ')}): {biomarker_names} | Product: {ingredient_names}"
    warnings = validate_profile_consistency(lab_data, state["profile"])
    warnings.extend(validate_expected_product_type(product_data, state.get("expected_product_type")))
    return {
        "extracted_summary": summary,
        "extracted_lab": lab_data,
        "extracted_product": product_data,
        "analysis": analysis,
        "confidence": confidence,
        "warnings": warnings,
        "underlying_clinical_attention": assess_underlying_clinical_attention(lab_data),
    }


def _text_check_node(state: GraphState) -> GraphState:
    text = state.get("ingredients_text") or ""
    analysis = analyze_text_ingredients(text, state["profile"])
    return {
        "extracted_summary": text,
        "analysis": analysis,
        "confidence": assess_text_confidence(text),
    }


def _confidence_route(state: GraphState) -> str:
    return "risk" if state["confidence"].can_show_verdict else "unable"


def _risk_node(state: GraphState) -> GraphState:
    score, verdict, color = calculate_hazard_score(state["analysis"].flags)
    return {"score": score, "verdict": verdict, "color": color}


def _arbiter_node(state: GraphState) -> GraphState:
    report = synthesize(
        profile=state["profile"],
        analysis=state["analysis"],
        score=state["score"],
        verdict=state["verdict"],
        color=state["color"],
        confidence=state["confidence"],
        fast_mode=state.get("fast_mode", False),
    )
    return {"report": report}


def _select_branch(state: GraphState) -> str:
    return state["mode"]


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("router", _router_node)
    graph.add_node("lab", _lab_node)
    graph.add_node("product", _product_node)
    graph.add_node("cross_match", _cross_match_node)
    graph.add_node("text_check", _text_check_node)
    graph.add_node("risk", _risk_node)
    graph.add_node("arbiter", _arbiter_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        _select_branch,
        {"lab": "lab", "product": "product", "cross_match": "cross_match", "text_check": "text_check"},
    )
    for node in ("lab", "product", "cross_match", "text_check"):
        graph.add_conditional_edges(node, _confidence_route, {"risk": "risk", "unable": END})
    graph.add_edge("risk", "arbiter")
    graph.add_edge("arbiter", END)
    return graph.compile()


_compiled_graph = None


def _low_confidence_output(mode: str, reason: str) -> PipelineOutput:
    return PipelineOutput(
        mode=mode,
        status="unable_to_assess",
        confidence=AnalysisConfidence(level="low", score=0, reasons=[reason], can_show_verdict=False),
        extracted_summary="",
    )


@traceable("chain", name="extracare.run_pipeline", tags=["workflow", "final-response"])
def run_pipeline(
    mode: str,
    profile: PatientProfile,
    image_bytes: Optional[bytes] = None,
    product_image_bytes: Optional[bytes] = None,
    ingredients_text: Optional[str] = None,
    fast_mode: bool = False,
    expected_product_type: Optional[str] = None,
) -> PipelineOutput:
    """Run one analysis. Known extraction/parsing failures return a fail-closed result."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()

    try:
        result: GraphState = _compiled_graph.invoke(
            {
                "mode": mode,
                "profile": profile,
                "image_bytes": image_bytes,
                "product_image_bytes": product_image_bytes,
                "ingredients_text": ingredients_text,
                "fast_mode": fast_mode,
                "expected_product_type": expected_product_type,
            }
        )
    except (AnalysisUnavailableError, OCRExtractionError) as exc:
        return _low_confidence_output(mode, str(exc))

    confidence = result["confidence"]
    report = result.get("report")
    status = "ok" if report is not None and confidence.can_show_verdict else "unable_to_assess"
    return PipelineOutput(
        mode=mode,
        status=status,
        report=report,
        confidence=confidence,
        extracted_summary=result.get("extracted_summary", ""),
        extracted_lab=result.get("extracted_lab"),
        extracted_product=result.get("extracted_product"),
        underlying_clinical_attention=result.get("underlying_clinical_attention"),
        retrieved_sources=result["analysis"].retrieved_sources,
        used_live_search=result["analysis"].used_live_search,
        warnings=result.get("warnings", []),
    )
