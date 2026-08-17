_SYSTEM_PROMPT = (
    "Eres un redactor inmobiliario. Describe la zona de una propiedad en 1-2 párrafos, "
    "en español, usando EXCLUSIVAMENTE los datos estructurados proporcionados. "
    "No inventes hospitales, comercios, precios ni valorizaciones que no estén en los datos. "
    "Si una categoría no tiene resultados, no la menciones como presente."
)


class NarrativeGenerator:
    def __init__(self, client, model: str = "claude-haiku-4-5-20251001"):
        self._client = client
        self._model = model

    def generate(self, report_data: dict) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=400,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": str(report_data)}],
        )
        return message.content[0].text


_CATEGORY_KEYWORDS = {
    "educacion": ["colegio", "escuela", "universidad"],
    "salud": ["hospital", "clínica", "farmacia"],
    "transporte": ["transporte", "estación", "parada"],
    "comercio": ["supermercado", "centro comercial"],
    "restaurantes": ["restaurante", "café"],
    "parques": ["parque"],
    "bancos": ["banco"],
}


def verify_groundedness(text: str, report_data: dict) -> bool:
    pois = report_data.get("pois", {})
    text_lower = text.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        has_data = len(pois.get(category, [])) > 0
        mentions_category = any(keyword in text_lower for keyword in keywords)
        if mentions_category and not has_data:
            return False
    return True
