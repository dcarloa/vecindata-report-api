from app.narrative.narrative import NarrativeGenerator, verify_groundedness


class _FakeContentBlock:
    def __init__(self, text):
        self.text = text


class _FakeMessage:
    def __init__(self, text):
        self.content = [_FakeContentBlock(text)]


class FakeAnthropicClient:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.messages = self

    def create(self, **kwargs):
        return _FakeMessage(self._response_text)


def test_generate_returns_text_from_client_response():
    fake_client = FakeAnthropicClient("Esta zona cuenta con buena conectividad.")
    generator = NarrativeGenerator(client=fake_client)
    result = generator.generate({"pois": {}})
    assert result == "Esta zona cuenta con buena conectividad."


def test_verify_groundedness_fails_when_text_mentions_absent_category():
    report_data = {"pois": {"salud": []}}
    text = "Cerca hay un hospital reconocido."
    assert verify_groundedness(text, report_data) is False


def test_verify_groundedness_passes_when_mentioned_categories_have_data():
    report_data = {"pois": {"parques": [{"name": "Parque X"}]}}
    text = "La zona cuenta con un parque cercano."
    assert verify_groundedness(text, report_data) is True
