"""Regression coverage for defects reproduced in the September 10 audit."""
import io
import json
from contextvars import ContextVar
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PIL import Image
from pydantic import ValidationError

from backend.core.analysis_utils import parse_analysis_response
from backend.core.confidence import assess_lab_confidence, assess_product_confidence
from backend.core.egfr import augment_with_egfr, calculate_egfr
from backend.core.errors import AnalysisParsingError
from backend.core.evidence_registry import is_source_verified
from backend.core.care_delta import compare_lab_results
from backend.core.disease_protocol_local import generate_local_disease_protocol
from backend.core.risk_engine import calculate_hazard_score
from backend.core.safety.clinical_attention import assess_underlying_clinical_attention
from backend.models.schemas import *

PROFILE = PatientProfile(age=55, gender="Female", chronic_conditions=["Celiac Disease"])

@pytest.mark.parametrize('payload', [{}, {'summary':'ok'}, {'flags':[]}, {'flags':[], 'summary':' '}])
def test_incomplete_analysis_cannot_become_safe(payload):
    with pytest.raises(AnalysisParsingError):
        parse_analysis_response(json.dumps(payload), base_tags=['rag'])

@pytest.mark.parametrize('value', [float('nan'),float('inf'),-float('inf')])
def test_nonfinite_lab_numbers_rejected(value):
    with pytest.raises(ValidationError): Biomarker(name='A',value=value)

@pytest.mark.parametrize('value',[0,-1,float('nan'),float('inf')])
def test_egfr_invalid_input_rejected(value):
    with pytest.raises(ValueError): calculate_egfr(value,55,'Female')

@pytest.mark.parametrize('name,unit,value,specimen',[
    ('Urine Creatinine','mg/dL',20,None),('Creatinine',None,1.2,None),
    ('Creatinine','mg/dL',1.2,'urine'),('Creatinine','mg/dL',0,None),
    ('Creatinine clearance','mg/dL',12,None),
])
def test_egfr_does_not_use_unknown_units_or_nonserum_values(name,unit,value,specimen):
    lab=ExtractedLabData(biomarkers=[Biomarker(name=name,unit=unit,value=value,specimen=specimen)])
    assert not augment_with_egfr(lab,PROFILE)

def test_egfr_augmentation_idempotent():
    lab=ExtractedLabData(biomarkers=[Biomarker(name='Serum Creatinine',unit='mg/dL',value=1.6)])
    assert augment_with_egfr(lab,PROFILE)
    assert not augment_with_egfr(lab,PROFILE)
    assert len(lab.biomarkers)==2

def test_attention_never_decreases_due_to_later_marker():
    lab=ExtractedLabData(biomarkers=[Biomarker(name='eGFR',value=14,unit='mL/min/1.73m2'),Biomarker(name='A',report_flag='High')])
    assert assess_underlying_clinical_attention(lab)=='high'

@pytest.mark.parametrize('name,value,unit',[('Creatinine',90,'umol/L'),('HbA1c',40,'mmol/mol'),('Hemoglobin',7,'mmol/L')])
def test_attention_does_not_apply_wrong_unit_threshold(name,value,unit):
    assert assess_underlying_clinical_attention(ExtractedLabData(biomarkers=[Biomarker(name=name,value=value,unit=unit)]))=='routine'

def test_empty_rows_and_blank_ingredients_blocked():
    assert not assess_lab_confidence(ExtractedLabData(biomarkers=[Biomarker(name='HbA1c')])).can_show_verdict
    assert not assess_product_confidence(ExtractedProductData(ingredients=[' '])).can_show_verdict

@pytest.mark.parametrize('term',['',' ','disease','Type 1 Diabetes'])
def test_local_disease_lookup_does_not_match_everything_or_wrong_subtype(term):
    assert not generate_local_disease_protocol(term).diagnostic_tests

def test_no_personalized_hazard_from_many_information_flags():
    flags=[ClinicalFlag(item=str(i),severity='info',mechanism='general only') for i in range(30)]
    assert calculate_hazard_score(flags)[:2]==(100,'Safe')

@pytest.mark.parametrize('label',['A','FDA','guidance','FAKE FDA food allergy guidance'])
def test_source_substrings_not_trusted(label):
    assert not is_source_verified(label)

def test_ai_cannot_assign_itself_deterministic_or_live_evidence():
    payload={'flags':[{'item':'eGFR','severity':'info','mechanism':'m','evidence_tags':['deterministic','live_search'],'source':'Imaginary'}],'summary':'s','retrieved_sources':['Imaginary']}
    result=parse_analysis_response(json.dumps(payload),base_tags=['rag'])
    assert result.flags[0].evidence_tags==['ai_synthesis']
    assert not result.retrieved_sources

def test_threshold_number_substring_is_insufficient():
    rule=RestrictionRule(condition='Celiac Disease',classification='partially_restricted',mechanism='m',tolerated_dose='2 mg/day',source='FDA food allergy guidance')
    a=AnalysisResult(flags=[ClinicalFlag(item='X',severity='caution',mechanism='m',restrictions=[rule])],summary='s')
    result=parse_analysis_response(a.model_dump_json(),base_tags=['rag'],context_chunks=['Source: FDA food allergy guidance. 20 ppm.'])
    assert result.flags[0].restrictions[0].tolerated_dose is None

def test_unknown_unit_and_inequality_deltas_not_comparable():
    old=ExtractedLabData(biomarkers=[Biomarker(name='X',value=10,unit='mg/dL')])
    for new in [Biomarker(name='X',value=20),Biomarker(name='X',value=20,unit='mg/dL',raw_value='>20')]:
        assert compare_lab_results(old,ExtractedLabData(biomarkers=[new])).items[0].direction=='not_comparable'

def test_jpeg_normalized_to_real_png():
    from backend.tools.pdf_utils import ensure_image_pages
    b=io.BytesIO(); Image.new('RGB',(24,24)).save(b,format='JPEG')
    assert ensure_image_pages(b.getvalue())[0].startswith(b'\x89PNG')

def test_threaded_tools_preserve_trace_context():
    from backend.core.tracing import TracedThreadPoolExecutor
    context=ContextVar('audit_context',default='lost'); context.set('parent-run')
    with TracedThreadPoolExecutor(max_workers=2) as pool:
        assert pool.submit(context.get).result()=='parent-run'

def test_arbiter_failure_preserves_specialist_report():
    from backend.agents.arbiter_agent import synthesize
    with patch('backend.agents.arbiter_agent.build_chat_model',side_effect=TimeoutError):
        out=synthesize(PROFILE,AnalysisResult(flags=[ClinicalFlag(item='X',severity='danger',mechanism='m')],summary='keep me'),35,'Toxic','danger',AnalysisConfidence(level='high',score=90))
    assert out.mechanism_summary=='keep me' and out.safety_score==35

def test_generic_quick_check_has_no_personalized_danger():
    from backend.agents.text_check_agent import analyze_text_ingredients
    a=analyze_text_ingredients('Gluten',PatientProfile(age=30,gender='Male'))
    assert a.flags and a.flags[0].severity=='info'

def test_partial_ingredient_word_does_not_match():
    from backend.core.restriction_engine import try_deterministic_restriction_check
    assert try_deterministic_restriction_check('tein',PROFILE) is None

def test_written_monitoring_interval_requires_evidence():
    from backend.core.safety.protocol_guard import validate_disease_protocol
    a=DiseaseProtocol(disease_name='X',diagnostic_tests=[DiagnosticTest(test_name='X',interval='weekly',reasoning='m')])
    validate_disease_protocol(a,'No interval supplied')
    assert a.diagnostic_tests[0].interval=='Individualized clinician-directed interval'

def test_doctor_brief_preserves_allergies():
    from backend.core.doctor_brief import build_doctor_brief
    p=PatientProfile(age=30,gender='Male',known_allergies=['Peanut'])
    out=PipelineOutput(mode='text_check',confidence=AnalysisConfidence(level='high',score=90),report=RiskReport(safety_score=70,verdict='Caution',color_code='caution',mechanism_summary='m',doctor_note='n'))
    assert 'Known allergies: Peanut' in build_doctor_brief(p,out)

@pytest.mark.parametrize('data',[
    ExtractedLabData(biomarkers=[Biomarker(name='A',value=1,unit='mg/dL')],was_truncated=True,pages_analyzed=1,pages_total=2),
    ExtractedLabData(biomarkers=[Biomarker(name='A',value=1,unit='mg/dL')],raw_text='Part of the report is unreadable'),
])
def test_incomplete_document_never_publishes_verdict(data):
    assert not assess_lab_confidence(data).can_show_verdict


def test_actual_groq_sdk_constructor_contract():
    from backend.config import settings
    from backend.tools.groq_client import build_chat_model
    with patch.object(settings, 'GROQ_API_KEY', 'offline-contract-test'):
        model = build_chat_model()
    assert model.max_retries == 2
    assert model.request_timeout == 60
    assert model.reasoning_format == 'hidden'
    assert model.reasoning_effort == 'none'
    assert model.model_name == 'qwen/qwen3.6-27b' 
