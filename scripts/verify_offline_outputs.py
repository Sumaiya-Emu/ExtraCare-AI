"""Record real local outputs without API calls, credentials, or substitute OCR."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.controllers.analysis_controller import analyze, build_visit_brief, generate_protocol
from backend.core.care_delta import compare_lab_results
from backend.models.schemas import Biomarker, ExtractedLabData, PatientProfile


def main():
    profile=PatientProfile(age=55,gender="Female",chronic_conditions=["Celiac Disease"],known_allergies=["Peanut Allergy"])
    celiac=analyze("text_check",profile,ingredients_text="Gluten",fast_mode=True)
    peanut=analyze("text_check",profile,ingredients_text="Peanut",fast_mode=True)
    general=analyze("text_check",PatientProfile(age=30,gender="Male"),ingredients_text="Gluten",fast_mode=True)
    assert celiac.status==peanut.status==general.status=="ok"
    assert celiac.report.verdict==peanut.report.verdict=="Toxic"
    assert general.report.safety_score==100 and general.report.flags[0].severity=="info"
    old=ExtractedLabData(biomarkers=[Biomarker(name="Creatinine",value=1.2,unit="mg/dL")])
    new=ExtractedLabData(biomarkers=[Biomarker(name="Creatinine",value=1.6,unit="mg/dL")])
    delta=compare_lab_results(old,new)
    assert delta.items[0].percent_change==33.3
    protocol=generate_protocol("Type 2 diabetes",fast_mode=True)
    assert protocol.diagnostic_tests
    output={"validation_type":"REAL LOCAL EXECUTION; no OCR, network, or cloud-model accuracy claim",
        "celiac_gluten":celiac.model_dump(),"peanut_allergy":peanut.model_dump(),
        "general_gluten_education":general.model_dump(),"synthetic_numeric_delta":delta.model_dump(),
        "local_diabetes_protocol":protocol.model_dump()}
    destination=ROOT/"docs"/"audit_evidence"; destination.mkdir(parents=True,exist_ok=True)
    (destination/"offline_outputs.json").write_text(json.dumps(output,indent=2),encoding="utf-8")
    (destination/"sample_doctor_brief.md").write_text(build_visit_brief(profile,celiac),encoding="utf-8")
    print("PASS: real local gluten/celiac, peanut/allergy, general-education, CareDelta and disease-hub outputs recorded.")

if __name__=="__main__": main()
