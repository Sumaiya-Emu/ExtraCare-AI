"""Type-safe data contracts shared across backend controllers and the Streamlit UI."""
from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(allow_inf_nan=False, str_strip_whitespace=True)


EvidenceKind = Literal["deterministic", "rag", "live_search", "ai_synthesis"]
RestrictionClass = Literal["fully_restricted", "partially_restricted"]
ProductType = Literal["food", "supplement", "medicine", "skincare", "cosmetic", "unknown"]
ExposureRoute = Literal["oral", "topical", "unknown"]
ClinicalAttention = Literal["routine", "follow_up", "high", "urgent_review"]


class PatientProfile(BaseModel):
    """Health context entered by the user and snapshotted with each analysis."""

    age: int = Field(..., ge=0, le=120)
    gender: Literal["Male", "Female"]
    is_pregnant: bool = False
    chronic_conditions: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    known_allergies: List[str] = Field(default_factory=list)


class Biomarker(BaseModel):
    """Numeric or qualitative laboratory observation.

    Real reports contain values such as ``Trace``, ``2+``, ``4-6 /HPF`` and comparison symbols,
    so the raw OCR text is preserved alongside an optional numeric representation.
    """

    name: str
    value: Optional[float] = None
    qualitative_value: Optional[str] = None
    raw_value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    specimen: Optional[str] = None
    report_flag: Optional[str] = None
    source_page: Optional[int] = Field(default=None, ge=1)


class RadiologyFinding(BaseModel):
    """Finding copied from a WRITTEN radiology report, not inferred from raw DICOM."""

    modality: Optional[Literal["X-Ray", "Ultrasound", "MRI", "CT", "Other"]] = None
    body_part: Optional[str] = None
    finding: str
    impression: Optional[str] = None
    abnormality: Optional[str] = None
    source_page: Optional[int] = Field(default=None, ge=1)


class ExtractedLabData(BaseModel):
    document_type: Literal[
        "blood_panel",
        "urinalysis",
        "radiology_report",
        "mixed",
        "unknown",
    ] = "unknown"
    reported_age: Optional[int] = Field(default=None, ge=0, le=120)
    reported_gender: Optional[Literal["Male", "Female"]] = None
    patient_name: Optional[str] = None
    biomarkers: List[Biomarker] = Field(default_factory=list)
    radiology_findings: List[RadiologyFinding] = Field(default_factory=list)
    raw_text: str = ""
    pages_analyzed: int = Field(default=1, ge=0)
    pages_total: int = Field(default=1, ge=0)
    was_truncated: bool = False


class ProductFact(BaseModel):
    """Structured nutrition / label fact where quantity is visibly printed."""

    name: str
    value: Optional[float] = None
    unit: Optional[str] = None
    per: Optional[str] = None
    raw_value: Optional[str] = None


class ExtractedProductData(BaseModel):
    product_name: Optional[str] = None
    product_type: ProductType = "unknown"
    exposure_route: ExposureRoute = "unknown"
    ingredients: List[str] = Field(default_factory=list)
    nutrition_facts: List[ProductFact] = Field(default_factory=list)
    allergen_statement: Optional[str] = None
    raw_text: str = ""
    pages_analyzed: int = Field(default=1, ge=0)
    pages_total: int = Field(default=1, ge=0)
    was_truncated: bool = False


class NutritionGuidance(BaseModel):
    item: str
    reason: str
    target_or_limit: Optional[str] = None
    source: Optional[str] = None


class DiagnosticTest(BaseModel):
    test_name: str
    interval: str
    reasoning: str
    source: Optional[str] = None


class DiseaseProtocol(BaseModel):
    """Educational condition-management roadmap, not a personalized prescription."""

    disease_name: str
    lifestyle_habits: List[str] = Field(default_factory=list)
    strict_restrictions: List[NutritionGuidance] = Field(default_factory=list)
    recommended_increases: List[NutritionGuidance] = Field(default_factory=list)
    diagnostic_tests: List[DiagnosticTest] = Field(default_factory=list)
    summary: str = ""
    evidence_sources: List[str] = Field(default_factory=list)
    used_live_search: bool = False


class RestrictionRule(BaseModel):
    """Condition-specific restriction with optional evidence-backed limits."""

    condition: str
    classification: RestrictionClass
    mechanism: str
    tolerated_dose: Optional[str] = None
    danger_threshold: Optional[str] = None
    observed_amount: Optional[str] = None
    threshold_status: Literal["within_limit", "near_limit", "exceeds_limit", "unknown"] = "unknown"
    source: Optional[str] = None


class ClinicalFlag(BaseModel):
    """One evidence-linked finding raised by a specialist agent."""

    item: str = Field(min_length=1)
    severity: Literal["info", "caution", "danger"]
    mechanism: str = Field(min_length=1)
    source: Optional[str] = None
    restrictions: List[RestrictionRule] = Field(default_factory=list)
    evidence_tags: List[EvidenceKind] = Field(default_factory=lambda: ["ai_synthesis"])
    evidence_note: Optional[str] = None
    restriction_type: Optional[RestrictionClass] = None


class AnalysisResult(BaseModel):
    flags: List[ClinicalFlag] = Field(default_factory=list)
    summary: str = ""
    retrieved_sources: List[str] = Field(default_factory=list)
    used_live_search: bool = False


class AnalysisConfidence(BaseModel):
    level: Literal["high", "medium", "low"]
    score: int = Field(..., ge=0, le=100)
    reasons: List[str] = Field(default_factory=list)
    can_show_verdict: bool = True


class SpecialistRecommendation(BaseModel):
    department: str
    rationale: str
    triggered_by: str
    priority: Literal["primary", "secondary"] = "secondary"


class RiskReport(BaseModel):
    """Final educational dossier shown to the user."""

    safety_score: int = Field(..., ge=0, le=100)
    verdict: Literal["Safe", "Caution", "Toxic"]
    color_code: str
    mechanism_summary: str
    doctor_note: str
    clinician_questions: List[str] = Field(default_factory=list)
    safe_alternatives: List[str] = Field(default_factory=list)
    flags: List[ClinicalFlag] = Field(default_factory=list)
    specialist_recommendations: List[SpecialistRecommendation] = Field(default_factory=list)
    confidence: Optional[AnalysisConfidence] = None


class CareGraphNode(BaseModel):
    id: str
    label: str
    kind: Literal["profile", "condition", "medication", "finding", "product", "evidence"]


class CareGraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    severity: Literal["info", "caution", "danger"] = "info"


class CareGraph(BaseModel):
    nodes: List[CareGraphNode] = Field(default_factory=list)
    edges: List[CareGraphEdge] = Field(default_factory=list)


class DeltaItem(BaseModel):
    name: str
    previous_value: Optional[float] = None
    current_value: Optional[float] = None
    previous_text: Optional[str] = None
    current_text: Optional[str] = None
    unit: Optional[str] = None
    direction: Literal["increased", "decreased", "unchanged", "changed", "new", "missing", "not_comparable"]
    percent_change: Optional[float] = None


class CareDelta(BaseModel):
    items: List[DeltaItem] = Field(default_factory=list)
    increased: int = 0
    decreased: int = 0
    unchanged: int = 0
    changed_qualitative: int = 0


class PipelineOutput(BaseModel):
    """Typed controller response; advanced UI features reuse this without re-running OCR."""

    mode: Literal["lab", "product", "cross_match", "text_check"]
    status: Literal["ok", "unable_to_assess"] = "ok"
    report: Optional[RiskReport] = None
    confidence: AnalysisConfidence
    extracted_summary: str = ""
    extracted_lab: Optional[ExtractedLabData] = None
    extracted_product: Optional[ExtractedProductData] = None
    underlying_clinical_attention: Optional[ClinicalAttention] = None
    retrieved_sources: List[str] = Field(default_factory=list)
    used_live_search: bool = False
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
