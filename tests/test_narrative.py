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


def test_verify_groundedness_flags_price_mentions_as_ungrounded():
    report_data = {"pois": {}}
    text = "El precio del metro cuadrado ronda los $4.500.000."
    assert verify_groundedness(text, report_data) is False


def test_verify_groundedness_does_not_flag_word_boundary_false_positive():
    report_data = {"pois": {"parques": []}}
    text = "El edificio cuenta con parqueadero para visitantes."
    assert verify_groundedness(text, report_data) is True


def test_verify_groundedness_conservatively_rejects_negated_absence_mention():
    # Documented trade-off: since negation parsing proved unreliable (it let
    # real fabrications through in adversarial testing), the checker no
    # longer exempts negated mentions. The system prompt is relied on
    # instead to avoid this phrasing; if the model uses it anyway, the
    # text is conservatively rejected rather than risking a fabrication.
    report_data = {"pois": {"salud": []}}
    text = "No hay hospitales ni clinicas cercanas."
    assert verify_groundedness(text, report_data) is False


def test_verify_groundedness_catches_plural_and_accent_variants():
    report_data = {"pois": {"restaurantes": []}}
    text = "Hay cafeterias y locales comerciales en el sector."
    assert verify_groundedness(text, report_data) is False


def test_generate_sends_grounding_instruction_in_system_prompt():
    captured = {}

    class CapturingClient:
        def __init__(self):
            self.messages = self

        def create(self, **kwargs):
            captured.update(kwargs)
            return _FakeMessage("Texto de prueba.")

    generator = NarrativeGenerator(client=CapturingClient())
    generator.generate({"pois": {}})
    assert "EXCLUSIVAMENTE" in captured["system"]
    assert "no inventes" in captured["system"].lower()


def test_verify_groundedness_does_not_leak_fabrication_across_clauses():
    report_data = {"pois": {"salud": [], "bancos": []}}
    text = "No hay bancos, pero hay clinicas modernas."
    assert verify_groundedness(text, report_data) is False


def test_verify_groundedness_sin_embargo_does_not_suppress_fabrication():
    report_data = {"pois": {"salud": []}}
    text = "Sin embargo, el hospital queda a cinco minutos."
    assert verify_groundedness(text, report_data) is False


def test_verify_groundedness_catches_repeated_keyword_not_just_first_occurrence():
    report_data = {"pois": {"salud": []}}
    text = "No hay farmacias en el barrio; las farmacias mas cercanas estan en la avenida."
    assert verify_groundedness(text, report_data) is False


def test_verify_groundedness_catches_transmilenio_fabrication():
    report_data = {"pois": {"transporte": []}}
    text = "La estacion de TransMilenio queda a dos cuadras."
    assert verify_groundedness(text, report_data) is False


def test_verify_groundedness_catches_broader_valuation_language():
    report_data = {"pois": {}}
    text = "El inmueble se cotiza en 500 millones y su arriendo es alto."
    assert verify_groundedness(text, report_data) is False


def test_verify_groundedness_price_keyword_respects_word_boundary():
    report_data = {"pois": {}}
    text = "Es un barrio de gran aprecio entre las familias."
    assert verify_groundedness(text, report_data) is True
