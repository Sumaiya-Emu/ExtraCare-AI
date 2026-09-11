"""Real graph/Chroma/UI execution with controlled external-service responses.

These checks establish integration behavior; they do not measure live Groq OCR accuracy.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from langchain_core.embeddings import Embeddings

from backend.config import settings
from backend.models.schemas import PatientProfile
from backend.controllers.analysis_controller import analyze

ROOT=Path(__file__).resolve().parents[1]
LAB={'document_type':'blood_panel','reported_age':55,'reported_gender':'Female','biomarkers':[{'name':'Serum Creatinine','value':1.6,'unit':'mg/dL','raw_value':'1.6'}],'raw_text':'Serum Creatinine 1.6 mg/dL'}
PRODUCT={'product_name':'Audit food','product_type':'food','exposure_route':'oral','ingredients':['Wheat','Salt','Oil'],'raw_text':'Wheat, Salt, Oil'}
ANALYSIS={'flags':[{'item':'Gluten','severity':'caution','mechanism':'Review the printed ingredient list with your clinician.','source':'FDA food allergy guidance'}],'summary':'Controlled integration output; not a live clinical assessment.'}
PROFILE=PatientProfile(age=55,gender='Female',chronic_conditions=['Celiac Disease'])

class LocalEmbeddings(Embeddings):
    """Deterministic test vectors; never wired into production."""
    def embed_documents(self,texts): return [self.embed_query(t) for t in texts]
    def embed_query(self,text):
        t=text.casefold()
        return [float(t.count(w))+0.1 for w in ['gluten','creatinine','sodium','diabetes','kidney','allergy','food','care']]

class Model:
    def invoke(self,prompt):
        if isinstance(prompt,list):
            txt=prompt[0].content[0]['text']
            payload=LAB if 'medical document extraction' in txt else PRODUCT
        elif 'final educational health-safety dossier' in prompt:
            payload={'mechanism_summary':'Controlled dossier','doctor_note':'Discuss original findings','clinician_questions':['What needs follow-up?'],'safe_alternatives':[]}
        elif 'general disease-care' in prompt:
            payload={'summary':'Controlled disease overview','lifestyle_habits':['Discuss the condition with a clinician'],'evidence_sources':[]}
        else: payload=ANALYSIS
        return SimpleNamespace(content=json.dumps(payload))

@pytest.fixture
def services(monkeypatch,tmp_path):
    from backend.rag import vector_store as v
    monkeypatch.setattr(settings,'GROQ_API_KEY','controlled-offline-test')
    monkeypatch.setattr(settings,'VECTOR_STORE_DIR',tmp_path/'vectors')
    monkeypatch.setattr(v,'_embeddings',LocalEmbeddings())
    monkeypatch.setattr(v,'_stores',{})
    monkeypatch.setattr(v,'_ingested',{})
    for module in ['ocr_tool']:
        monkeypatch.setattr('backend.tools.'+module+'.build_chat_model',lambda **kw:Model())
    for module in ['lab_agent','product_agent','cross_match_agent','text_check_agent','arbiter_agent','disease_hub_agent']:
        monkeypatch.setattr('backend.agents.'+module+'.build_chat_model',lambda **kw:Model())
    return v

@pytest.mark.parametrize('mode,fast,kind',[('lab',True,None),('lab',False,None),('product',True,None),('product',False,None),('cross_match',True,'food'),('cross_match',False,'food'),('text_check',True,None),('text_check',False,None)])
def test_complete_graph_modes(services,mode,fast,kind):
    lab=(ROOT/'data/sample_images/sample_blood_test.png').read_bytes()
    food=(ROOT/'data/sample_images/sample_food_label.png').read_bytes()
    out=analyze(mode,PROFILE,image_bytes=food if mode=='product' else lab,product_image_bytes=food,ingredients_text='Wheat flour',fast_mode=fast,expected_product_type=kind)
    assert out.status=='ok',out.model_dump()
    assert out.report and out.report.safety_score==70
    assert out.report.verdict=='Caution'
    if mode in {'lab','cross_match'}:
        assert out.extracted_lab.biomarkers[-1].name.startswith('eGFR (calculated')
    if mode in {'lab','product','cross_match'}: assert out.retrieved_sources


def test_ingestion_is_idempotent_updates_and_repairs(services,tmp_path,monkeypatch):
    v=services
    v.ingest_knowledge_base(); s=v.get_vector_store(settings.CLINICAL_COLLECTION)
    count=len(s.get()['ids']); assert count==14
    v.ingest_knowledge_base(force=True); assert len(s.get()['ids'])==count
    # A missing record after an interrupted process is filled on the next startup.
    s.delete(ids=[s.get()['ids'][0]]); v._ingested.clear(); v.ingest_knowledge_base()
    assert len(s.get()['ids'])==count
    source=tmp_path/'kb'; source.mkdir()
    for f in settings.KNOWLEDGE_BASE_DIR.glob('*.json'): (source/f.name).write_bytes(f.read_bytes())
    f=source/'clinical_guidelines.json'; entries=json.loads(f.read_text()); entries=entries[:-1]; f.write_text(json.dumps(entries))
    monkeypatch.setattr(settings,'KNOWLEDGE_BASE_DIR',source); v.ingest_knowledge_base()
    assert len(s.get()['ids'])==count-1


def test_empty_ai_json_produces_blocked_pipeline(services,monkeypatch):
    monkeypatch.setattr('backend.agents.lab_agent.build_chat_model',lambda:SimpleNamespace(invoke=lambda _:SimpleNamespace(content='{}')))
    out=analyze('lab',PROFILE,image_bytes=(ROOT/'data/sample_images/sample_blood_test.png').read_bytes(),fast_mode=True)
    assert out.status=='unable_to_assess' and out.report is None


def test_wrong_cross_match_input_blocked(services):
    out=analyze('cross_match',PROFILE,image_bytes=(ROOT/'data/sample_images/sample_blood_test.png').read_bytes(),product_image_bytes=(ROOT/'data/sample_images/sample_food_label.png').read_bytes(),expected_product_type='skincare',fast_mode=True)
    assert out.status=='unable_to_assess'


def test_search_results_reach_user_output(services,monkeypatch):
    import backend.agents.product_agent as product
    monkeypatch.setattr(product,'is_available',lambda:True)
    monkeypatch.setattr(product,'search_web',lambda q:[{'title':'Controlled recall result','url':'https://example.org/test-recall','content':'Test fixture only.'}])
    out=analyze('product',PROFILE,image_bytes=(ROOT/'data/sample_images/sample_food_label.png').read_bytes(),fast_mode=False)
    assert out.status=='ok' and out.used_live_search
    assert 'https://example.org/test-recall' in out.retrieved_sources


def test_disease_hub_thorough_path(services):
    from backend.controllers.analysis_controller import generate_protocol
    out=generate_protocol('Celiac Disease',fast_mode=False)
    assert out.summary=='Controlled disease overview'


def app(path):
    from streamlit.testing.v1 import AppTest
    if str(ROOT/'frontend') not in sys.path: sys.path.insert(0,str(ROOT/'frontend'))
    return AppTest.from_file(str(ROOT/path),default_timeout=30).run()

@pytest.mark.parametrize('path',['frontend/app.py',*[str(p.relative_to(ROOT)) for p in sorted((ROOT/'frontend/pages').glob('*.py'))]])
def test_every_streamlit_page_starts(path):
    at=app(path)
    assert not at.exception,[e.message for e in at.exception]


def test_ui_real_local_quick_check_and_clear_input():
    at=app('frontend/pages/5_Quick_Ingredient_Check.py')
    at.multiselect(key='profile_conditions').set_value(['Celiac Disease']).run()
    at.text_area(key='text_check_input').set_value('Gluten').run()
    at.button(key='text_check_analyze').click().run()
    assert not at.exception,[e.message for e in at.exception]
    assert at.session_state['quick_text_result'].status=='ok'
    assert at.session_state['quick_text_result'].report.verdict=='Toxic'
    at.text_area(key='text_check_input').set_value('').run()
    assert 'quick_text_result' not in at.session_state


def test_ui_pipeline_retry_after_service_failure(services,monkeypatch):
    at=app('frontend/pages/1_Lab_Decoder.py')
    at.number_input(key='profile_age').set_value(55).run()
    at.button(key='lab_sample').click().run()
    import backend.agents.lab_agent as agent
    real=agent.build_chat_model
    monkeypatch.setattr(agent,'build_chat_model',lambda:SimpleNamespace(invoke=lambda _:SimpleNamespace(content='{}')))
    at.button(key='lab_analyze').click().run()
    assert at.session_state['lab_report_result'].status=='unable_to_assess'
    monkeypatch.setattr(agent,'build_chat_model',real)
    at.button(key='lab_analyze').click().run()
    assert not at.exception,[e.message for e in at.exception]
    assert at.session_state['lab_report_result'].status=='ok'


def test_clear_timeline_also_removes_results_and_upload_bytes():
    at=app('frontend/pages/7_My_Health_Timeline.py')
    at.session_state['lab_report_result']='old sensitive report'
    at.session_state['lab_image_bytes']=b'old sensitive image'
    next(b for b in at.button if b.label=='Clear session health memory').click().run()
    assert not at.exception
    assert 'lab_report_result' not in at.session_state and 'lab_image_bytes' not in at.session_state


def test_upload_removal_invalidates_bytes_and_result(monkeypatch):
    if str(ROOT/'frontend') not in sys.path: sys.path.insert(0,str(ROOT/'frontend'))
    import ui_common
    state={}
    monkeypatch.setattr(ui_common.st,'session_state',state)
    uploaded=SimpleNamespace(file_id='1',getvalue=lambda:b'uploaded image')
    ui_common.sync_uploaded_document(uploaded,'bytes','id','result')
    state['result']='old analysis'
    ui_common.sync_uploaded_document(None,'bytes','id','result')
    assert 'bytes' not in state and 'result' not in state


def test_selected_sample_survives_upload_removal(monkeypatch):
    if str(ROOT/'frontend') not in sys.path: sys.path.insert(0,str(ROOT/'frontend'))
    import ui_common
    state={'bytes':b'sample','bytes_source':'sample','id':'old upload'}
    monkeypatch.setattr(ui_common.st,'session_state',state)
    ui_common.sync_uploaded_document(None,'bytes','id','result')
    assert state['bytes']==b'sample' and 'id' not in state
