from core.intent import emergency_score
from modules.emergency import is_emergency


def test_emergency_score():
    text = "My dog is having a seizure and trouble breathing."
    score = emergency_score(text)
    assert score > 0
    assert is_emergency(text, threshold=3.0)
