import unicodedata

_SYSTEM_PROMPT = (
    "Eres un redactor inmobiliario. Describe la zona de una propiedad en 1-2 párrafos, "
    "en español, usando EXCLUSIVAMENTE los datos estructurados proporcionados. "
    "No inventes hospitales, comercios, precios ni valorizaciones que no estén en los datos. "
    "No menciones precios, valorizaciones, avalúos ni cifras en pesos o porcentajes bajo ninguna circunstancia. "
    "Si una categoría no tiene resultados, simplemente omítela del texto — no la menciones "
    "ni en positivo ni en negativo (evita frases como 'no hay parques cercanos')."
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


def _normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in stripped if not unicodedata.combining(c))


_CATEGORY_KEYWORDS = {
    "educacion": [
        "colegio", "colegios", "escuela", "escuelas", "universidad", "universidades",
        "institucion educativa", "instituciones educativas", "jardin infantil", "jardines infantiles",
    ],
    "salud": [
        "hospital", "hospitales", "clinica", "clinicas", "farmacia", "farmacias",
        "centro medico", "centros medicos", "consultorio", "consultorios",
    ],
    "transporte": [
        "estacion de transporte", "estaciones de transporte", "estacion de metro", "estaciones de metro",
        "parada de bus", "paradas de bus", "transporte publico",
    ],
    "comercio": [
        "supermercado", "supermercados", "centro comercial", "centros comerciales", "comercio", "comercios",
    ],
    "restaurantes": ["restaurante", "restaurantes", "cafeteria", "cafeterias"],
    "parques": ["parque", "parques"],
    "bancos": [
        "banco", "bancos", "sucursal bancaria", "sucursales bancarias",
        "cajero automatico", "cajeros automaticos",
    ],
}

_NEGATION_TRIGGERS = ["no hay", "sin ", "no existen", "no se registran", "no cuenta con", "carece de"]

_PRICE_KEYWORDS = [
    "precio", "precios", "valorizacion", "valorizaciones", "avaluo", "avaluos",
    "costo", "$", "%", "m2", "pesos",
]


def _mentions_ungrounded_keyword(text_normalized: str, keyword: str) -> bool:
    import re

    match = re.search(r"\b" + re.escape(keyword) + r"\b", text_normalized)
    if not match:
        return False
    window = text_normalized[max(0, match.start() - 25):match.start()]
    if any(trigger in window for trigger in _NEGATION_TRIGGERS):
        return False
    return True


def verify_groundedness(text: str, report_data: dict) -> bool:
    """
    Heuristic, category-presence-only groundedness check for the AI-written
    narrative. Two things make text "ungrounded":

    1. A category-related keyword appears (and isn't just a negated mention,
       e.g. "no hay parques cercanos" is allowed) while that category has
       zero POIs in report_data.
    2. Any price/valuation-related keyword appears at all — report_data
       never contains price data in this version, so any such mention is
       necessarily fabricated.

    Known limitation: this is category-presence matching, not entity
    verification. If a category has at least one real POI, this check
    cannot detect an invented NAME for a different place in that category
    (e.g. an invented "Hospital San Ignacio" is not caught as long as some
    real salud POI exists). It also does not exhaustively cover every way
    to reference a category in Spanish (e.g. bare "metro" is intentionally
    excluded from transporte keywords because it collides with "metros
    cuadrados", a common area unit — this is an accepted gap, not a bug).
    """
    pois = report_data.get("pois", {})
    text_normalized = _normalize(text)

    for price_keyword in _PRICE_KEYWORDS:
        if _normalize(price_keyword) in text_normalized:
            return False

    for category, keywords in _CATEGORY_KEYWORDS.items():
        has_data = len(pois.get(category, [])) > 0
        if has_data:
            continue
        for keyword in keywords:
            if _mentions_ungrounded_keyword(text_normalized, _normalize(keyword)):
                return False

    return True
