"""Pure-Python regression tests for ExtraCare AI core logic (no API keys required)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config.catalog import CONDITION_OPTIONS
from backend.core.analysis_utils import parse_analysis_response
from backend.core.care_delta import compare_lab_results
from backend.core.care_graph import build_care_graph, care_graph_to_dot
from backend.core.disease_protocol_local import generate_local_disease_protocol
from backend.core.confidence import assess_lab_confidence, assess_product_confidence, assess_text_confidence
from backend.core.errors import AnalysisParsingError
from backend.core.egfr import augment_with_egfr, calculate_egfr, stage_from_egfr
from backend.core.json_extract import extract_json_object
from backend.core.query_builder import adaptive_retrieval_k
from backend.core.restriction_engine import try_deterministic_restriction_check
from backend.core.risk_engine import calculate_hazard_score
from backend.core.specialist_map import recommend_specialist, recommend_specialists
from backend.models.schemas import (
    Biomarker,
    ClinicalFlag,
    ExtractedLabData,
    ExtractedProductData,
    PatientProfile,
    RestrictionRule,
    RiskReport,
)
from backend.tools.pdf_utils import ensure_image_bytes, is_pdf, pdf_to_image_pages


def test_profile_schema_valid():
    profile = PatientProfile(age=55, gender="Male", chronic_conditions=["Hypertension"])
    assert profile.age == 55
    assert profile.is_pregnant is False


def test_qualitative_urinalysis_value_supported():
    marker = Biomarker(name="Urine Protein", qualitative_value="Trace", specimen="urine")
    assert marker.value is None
    assert marker.qualitative_value == "Trace"


def test_restriction_schema_supports_graduated_rules():
    full = RestrictionRule(
        condition="Celiac Disease",
        classification="fully_restricted",
        mechanism="Autoimmune trigger",
        tolerated_dose="Verified gluten-free labeling context",
    )
    partial = RestrictionRule(
        condition="Hypertension",
        classification="partially_restricted",
        mechanism="Dose-dependent sodium load",
    )
    assert full.classification == "fully_restricted"
    assert partial.danger_threshold is None


def test_egfr_age_and_sex_change_result():
    assert calculate_egfr(1.6, 70, "Female") < calculate_egfr(1.6, 30, "Female")
    assert calculate_egfr(1.0, 50, "Male") != calculate_egfr(1.0, 50, "Female")


def test_egfr_shipped_sample_is_stage_g3b():
    egfr = calculate_egfr(1.6, 55, "Female")
    assert 35 < egfr < 41
    assert stage_from_egfr(egfr) == "G3b (moderately-severely decreased)"


def test_egfr_not_added_under_18_or_pregnancy():
    base = ExtractedLabData(
        document_type="blood_panel",
        biomarkers=[Biomarker(name="Serum Creatinine", value=1.2, unit="mg/dL")],
    )
    child = base.model_copy(deep=True)
    pregnant = base.model_copy(deep=True)
    assert augment_with_egfr(child, PatientProfile(age=12, gender="Male")) is False
    assert augment_with_egfr(pregnant, PatientProfile(age=30, gender="Female", is_pregnant=True)) is False
    assert len(child.biomarkers) == 1
    assert len(pregnant.biomarkers) == 1


def test_egfr_refuses_clearly_wrong_units():
    data = ExtractedLabData(
        document_type="blood_panel",
        biomarkers=[Biomarker(name="Creatinine", value=90, unit="µmol/L")],
    )
    assert augment_with_egfr(data, PatientProfile(age=50, gender="Male")) is False


def test_json_extract_regressions():
    assert extract_json_object('{"a": 1}') == {"a": 1}
    assert extract_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    text = '{"flags": [], "summary": "ok"} note {age: 55}'
    assert extract_json_object(text) == {"flags": [], "summary": "ok"}
    provider_content = [{"type": "text", "text": '{"flags": [], "summary": "ok"}', "extras": {"signature": "x"}}]
    assert extract_json_object(provider_content) == {"flags": [], "summary": "ok"}


def test_confidence_gate_blocks_empty_extractions():
    lab = assess_lab_confidence(ExtractedLabData())
    product = assess_product_confidence(ExtractedProductData())
    assert lab.level == "low" and not lab.can_show_verdict
    assert product.level == "low" and not product.can_show_verdict
    assert assess_text_confidence("Gluten").can_show_verdict


def test_confidence_valid_lab_is_showable():
    data = ExtractedLabData(
        document_type="blood_panel",
        biomarkers=[Biomarker(name="HbA1c", value=7.2, unit="%", reference_range="<5.7%")],
    )
    conf = assess_lab_confidence(data)
    assert conf.level == "high"
    assert conf.can_show_verdict


def test_hazard_score_behaviour():
    score, verdict, _ = calculate_hazard_score([])
    assert (score, verdict) == (100, "Safe")
    score, verdict, _ = calculate_hazard_score([ClinicalFlag(item="A", severity="danger", mechanism="m")])
    assert verdict == "Toxic" and score <= 35
    score, verdict, _ = calculate_hazard_score([ClinicalFlag(item="A", severity="caution", mechanism="m")])
    assert verdict == "Caution" and score <= 70


def test_pdf_multi_page_rendering():
    import pymupdf

    doc = pymupdf.open()
    for i in range(3):
        page = doc.new_page()
        page.insert_text((50, 50), f"Page {i + 1}: diagnostic findings", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()

    assert is_pdf(pdf_bytes)
    pages = pdf_to_image_pages(pdf_bytes, max_pages=8)
    assert len(pages) == 3
    assert all(p[:8] == b"\x89PNG\r\n\x1a\n" for p in pages)
    assert ensure_image_bytes(pdf_bytes)[:8] == b"\x89PNG\r\n\x1a\n"


def test_specialist_engine_multiple_domains():
    flags = [
        ClinicalFlag(item="UACR", severity="danger", mechanism="Severely increased albuminuria with kidney risk"),
        ClinicalFlag(item="HbA1c", severity="danger", mechanism="Glycemic control requires diabetes review"),
        ClinicalFlag(item="Mild hepatomegaly", severity="caution", mechanism="Written ultrasound liver finding"),
    ]
    recs = recommend_specialists(flags)
    departments = [r.department for r in recs]
    assert "Nephrology" in departments
    assert "Endocrinology" in departments
    assert "Hepatology / Gastroenterology" in departments
    assert recs[0].priority == "primary"


def test_specialist_danger_wins_over_caution():
    flags = [
        ClinicalFlag(item="Sodium", severity="caution", mechanism="raises blood pressure"),
        ClinicalFlag(item="HbA1c", severity="danger", mechanism="diabetes"),
    ]
    specialist, _ = recommend_specialist(flags)
    assert specialist == "Endocrinology"


def test_joint_degeneration_maps_to_orthopedics():
    recs = recommend_specialists([ClinicalFlag(item="Lumbar report", severity="caution", mechanism="degenerative changes L4-L5")])
    assert recs and recs[0].department == "Orthopedics"


def test_care_delta_numeric_and_qualitative():
    old = ExtractedLabData(
        document_type="mixed",
        biomarkers=[
            Biomarker(name="Creatinine", value=1.2, unit="mg/dL"),
            Biomarker(name="Urine Protein", qualitative_value="Trace"),
        ],
    )
    new = ExtractedLabData(
        document_type="mixed",
        biomarkers=[
            Biomarker(name="Creatinine", value=1.6, unit="mg/dL"),
            Biomarker(name="Urine Protein", qualitative_value="2+"),
        ],
    )
    delta = compare_lab_results(old, new)
    assert delta.increased == 1
    assert delta.changed_qualitative == 1
    creatinine = next(i for i in delta.items if i.name == "Creatinine")
    assert creatinine.percent_change == 33.3


def test_care_graph_connects_restriction_to_condition():
    restriction = RestrictionRule(
        condition="Celiac Disease",
        classification="fully_restricted",
        mechanism="Autoimmune trigger",
    )
    flag = ClinicalFlag(item="Gluten", severity="danger", mechanism="Relevant to celiac", restrictions=[restriction])
    report = RiskReport(
        safety_score=35,
        verdict="Toxic",
        color_code="#000000",
        mechanism_summary="m",
        doctor_note="n",
        flags=[flag],
    )
    graph = build_care_graph(PatientProfile(age=30, gender="Female", chronic_conditions=["Celiac Disease"]), report)
    assert any(e.relation == "avoid" for e in graph.edges)
    assert "Gluten" in care_graph_to_dot(graph)



def test_malformed_analysis_fails_closed():
    try:
        parse_analysis_response("not-json", base_tags=["rag"], context_chunks=[])
    except AnalysisParsingError:
        pass
    else:
        raise AssertionError("Malformed analysis must fail closed, not become empty Safe flags")


def test_numeric_restriction_is_removed_without_matching_retrieved_evidence():
    content = '{"flags":[{"item":"Ingredient X","severity":"caution","mechanism":"m","source":"Imaginary source","restrictions":[{"condition":"Hypertension","classification":"partially_restricted","mechanism":"m","tolerated_dose":"1234 mg/day","danger_threshold":null,"observed_amount":null,"threshold_status":"unknown","source":"Imaginary source"}]}],"summary":"s"}'
    result = parse_analysis_response(content, base_tags=["rag"], context_chunks=["Source: Imaginary source. No numeric dose stated."])
    assert result.flags[0].restrictions[0].tolerated_dose is None


def test_deterministic_quick_check_fast_path_for_celiac_gluten():
    profile = PatientProfile(age=30, gender="Female", chronic_conditions=["Celiac Disease"])
    result = try_deterministic_restriction_check("Gluten", profile)
    assert result is not None
    assert result.flags[0].restrictions[0].classification == "fully_restricted"
    assert result.flags[0].evidence_tags == ["deterministic"]


def test_deterministic_fast_path_falls_back_for_unknown_or_uncovered_condition():
    profile = PatientProfile(age=30, gender="Male", chronic_conditions=["Hypertension"])
    assert try_deterministic_restriction_check("Mystery Ingredient", profile) is None
    # Gluten is known, but its curated restriction is not a hypertension rule; absence is not proof of safety.
    assert try_deterministic_restriction_check("Gluten", profile) is None

def test_adaptive_retrieval_k_scales():
    assert adaptive_retrieval_k(3) == 4
    assert 4 < adaptive_retrieval_k(100) <= 12


def test_every_condition_option_has_backing_data():
    base = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"
    clinical = json.load(open(base / "clinical_guidelines.json", encoding="utf-8"))
    toxicology = json.load(open(base / "toxicology_standards.json", encoding="utf-8"))
    clinical_conditions = {e["condition"] for e in clinical if "condition" in e}
    toxicology_conditions = {c for e in toxicology if "flagged_conditions" in e for c in e["flagged_conditions"]}
    backed = clinical_conditions | toxicology_conditions
    assert not [c for c in CONDITION_OPTIONS if c not in backed]


def test_uacr_reference_present():
    base = Path(__file__).resolve().parent.parent / "data" / "knowledge_base" / "clinical_guidelines.json"
    clinical = json.load(open(base, encoding="utf-8"))
    entry = next(e for e in clinical if e.get("biomarker") == "Urine Albumin-to-Creatinine Ratio (UACR)")
    assert "30-300 mg/g" in entry["caution_range"]


def test_specialist_alt_does_not_match_sea_salt():
    flags = [
        ClinicalFlag(
            item="Sea salt",
            severity="caution",
            mechanism="Sodium load may worsen fluid retention in reduced kidney function.",
            restrictions=[
                RestrictionRule(
                    condition="Chronic Kidney Disease (CKD)",
                    classification="partially_restricted",
                    mechanism="Dose-dependent sodium concern",
                )
            ],
        )
    ]
    departments = [r.department for r in recommend_specialists(flags)]
    assert "Hepatology / Gastroenterology" not in departments


def test_cardio_not_triggered_by_downstream_cardiac_wording_alone():
    flags = [
        ClinicalFlag(
            item="Russet potatoes",
            severity="caution",
            mechanism="Potassium accumulation can have cardiac complications in severe renal dysfunction.",
            restrictions=[
                RestrictionRule(
                    condition="Chronic Kidney Disease (CKD)",
                    classification="partially_restricted",
                    mechanism="Renal potassium handling is impaired.",
                )
            ],
        )
    ]
    departments = [r.department for r in recommend_specialists(flags, PatientProfile(age=62, gender="Male"))]
    assert "Nephrology" in departments
    assert "Cardiology" not in departments


def test_fast_disease_protocol_uses_local_kb_without_numeric_invention():
    protocol = generate_local_disease_protocol("Diabetes Mellitus (Type 2)")
    assert len(protocol.diagnostic_tests) >= 2
    assert all(t.interval == "Individualized clinician-directed interval" for t in protocol.diagnostic_tests)
    assert protocol.used_live_search is False



def test_profile_consistency_blocks_explicit_age_mismatch():
    from backend.core.errors import AnalysisUnavailableError
    from backend.core.safety.input_guard import validate_profile_consistency

    lab = ExtractedLabData(reported_age=62, reported_gender="Male")
    try:
        validate_profile_consistency(lab, PatientProfile(age=30, gender="Male"))
    except AnalysisUnavailableError:
        pass
    else:
        raise AssertionError("Explicit report/profile age mismatch must fail closed")


def test_profile_consistency_warns_when_report_demographics_absent():
    from backend.core.safety.input_guard import validate_profile_consistency

    warnings = validate_profile_consistency(ExtractedLabData(), PatientProfile(age=30, gender="Female"))
    assert warnings and "could not be cross-verified" in warnings[0]


def test_wrong_cross_match_product_type_is_blocked():
    from backend.core.errors import AnalysisUnavailableError
    from backend.core.safety.input_guard import validate_expected_product_type

    product = ExtractedProductData(product_type="skincare", exposure_route="topical", ingredients=["Glycerin"])
    try:
        validate_expected_product_type(product, "food")
    except AnalysisUnavailableError:
        pass
    else:
        raise AssertionError("Skincare input must not pass the Food Cross-Match type gate")


def test_unknown_product_type_is_warning_not_false_block():
    from backend.core.safety.input_guard import validate_expected_product_type

    warnings = validate_expected_product_type(ExtractedProductData(product_type="unknown"), "food")
    assert warnings


def test_general_condition_rule_is_not_personalized_danger():
    from backend.core.safety.personalization import demote_general_only_flags
    from backend.models.schemas import AnalysisResult

    result = AnalysisResult(
        flags=[
            ClinicalFlag(
                item="Gluten",
                severity="danger",
                mechanism="Relevant only to celiac disease",
                restrictions=[
                    RestrictionRule(
                        condition="Celiac Disease",
                        classification="fully_restricted",
                        mechanism="Autoimmune trigger",
                    )
                ],
            )
        ]
    )
    demote_general_only_flags(result, PatientProfile(age=30, gender="Male"))
    assert result.flags[0].severity == "info"


def test_topical_route_guard_demotes_oral_dietary_claim():
    from backend.core.safety.product_claims import validate_product_claims
    from backend.models.schemas import AnalysisResult

    product = ExtractedProductData(
        product_type="skincare",
        exposure_route="topical",
        ingredients=["Potassium phosphate"],
        raw_text="Moisturizer. Ingredients: potassium phosphate.",
    )
    result = AnalysisResult(
        flags=[
            ClinicalFlag(
                item="Potassium phosphate",
                severity="danger",
                mechanism="Dietary intake of potassium may be restricted in kidney disease.",
            )
        ]
    )
    validate_product_claims(result, product)
    assert result.flags[0].severity == "info"


def test_product_observed_amount_must_exist_on_label():
    from backend.core.safety.product_claims import validate_product_claims
    from backend.models.schemas import AnalysisResult

    product = ExtractedProductData(
        product_type="food",
        exposure_route="oral",
        ingredients=["Sea salt"],
        nutrition_facts=[],
        raw_text="Ingredients: potatoes, canola oil, sea salt",
    )
    rule = RestrictionRule(
        condition="Hypertension",
        classification="partially_restricted",
        mechanism="Sodium context",
        observed_amount="999 mg",
        threshold_status="exceeds_limit",
    )
    result = AnalysisResult(flags=[ClinicalFlag(item="Sea salt", severity="caution", mechanism="m", restrictions=[rule])])
    validate_product_claims(result, product)
    assert rule.observed_amount is None
    assert rule.threshold_status == "unknown"


def test_underlying_clinical_attention_separate_from_interaction_score():
    from backend.core.safety.clinical_attention import assess_underlying_clinical_attention

    lab = ExtractedLabData(
        document_type="blood_panel",
        biomarkers=[Biomarker(name="eGFR", value=14, unit="mL/min/1.73m2", report_flag="Low")],
    )
    assert assess_underlying_clinical_attention(lab) == "high"


def test_caredelta_refuses_numeric_comparison_when_units_differ():
    old = ExtractedLabData(biomarkers=[Biomarker(name="Creatinine", value=1.2, unit="mg/dL")])
    new = ExtractedLabData(biomarkers=[Biomarker(name="Creatinine", value=106, unit="umol/L")])
    delta = compare_lab_results(old, new)
    assert delta.items[0].direction == "not_comparable"
    assert delta.items[0].percent_change is None


def test_unverified_source_cannot_drive_absolute_restriction():
    content = '{"flags":[{"item":"X","severity":"danger","mechanism":"m","source":"General clinical reference","restrictions":[{"condition":"Pregnancy","classification":"fully_restricted","mechanism":"m","tolerated_dose":null,"danger_threshold":null,"observed_amount":null,"threshold_status":"unknown","source":"General clinical reference"}]}],"summary":"s"}'
    result = parse_analysis_response(content, base_tags=["rag"], context_chunks=["Source: General clinical reference. Educational note."])
    assert result.flags[0].restrictions[0].classification == "partially_restricted"
    assert result.flags[0].severity == "caution"


def test_protocol_guard_removes_unsupported_precision():
    from backend.core.safety.protocol_guard import validate_disease_protocol
    from backend.models.schemas import DiagnosticTest, DiseaseProtocol, NutritionGuidance

    protocol = DiseaseProtocol(
        disease_name="Demo",
        strict_restrictions=[NutritionGuidance(item="Salt", reason="r", target_or_limit="1234 mg/day", source="Made Up")],
        diagnostic_tests=[DiagnosticTest(test_name="Test", interval="every 3 months", reasoning="r", source="Made Up")],
        evidence_sources=["Made Up"],
    )
    validate_disease_protocol(protocol, "No numeric target or interval is supplied here.")
    assert protocol.strict_restrictions[0].target_or_limit is None
    assert protocol.diagnostic_tests[0].interval == "Individualized clinician-directed interval"
    assert protocol.evidence_sources == []


def test_fda_peanut_rule_is_verified_absolute_restriction():
    from backend.core.evidence_registry import allows_absolute_restriction

    assert allows_absolute_restriction("FDA food allergy guidance")
    profile = PatientProfile(age=30, gender="Female", known_allergies=["Peanut Allergy"])
    result = try_deterministic_restriction_check("Peanut", profile)
    assert result is not None
    assert result.flags[0].severity == "danger"
    assert result.flags[0].restrictions[0].classification == "fully_restricted"


def test_ckd_potassium_rule_is_not_absolute_without_verified_absolute_source():
    profile = PatientProfile(age=62, gender="Male", chronic_conditions=["Chronic Kidney Disease (CKD)"])
    result = try_deterministic_restriction_check("Potassium Chloride", profile)
    assert result is not None
    assert result.flags[0].severity == "caution"
    assert result.flags[0].restrictions[0].classification == "partially_restricted"


if __name__ == "__main__":
    tests = [name for name, value in globals().copy().items() if name.startswith("test_") and callable(value)]
    for name in sorted(tests):
        globals()[name]()
    print(f"ALL {len(tests)} CORE TESTS PASSED")
