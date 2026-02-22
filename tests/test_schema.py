from core.response import VetResponse


def test_vet_response_schema_enforced():
    payload = {
        "answer": "A",
        "possible_causes": "B",
        "warning_signs": "C",
        "vet_visit_guidance": "D",
        "care_tips": "E",
        "citations": [],
    }
    model = VetResponse.model_validate(payload)
    assert model.answer == "A"
