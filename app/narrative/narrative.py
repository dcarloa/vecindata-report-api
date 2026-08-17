import json
import re
import unicodedata

from google.genai import types

_SYSTEM_PROMPT = (
    "Eres un redactor inmobiliario. Describe la zona de una propiedad en 1-2 párrafos, "
    "en español, usando EXCLUSIVAMENTE los datos estructurados proporcionados. "
    "No inventes hospitales, comercios, precios ni valorizaciones que no estén en los datos. "
    "No menciones precios, valorizaciones, avalúos ni cifras en pesos o porcentajes bajo ninguna circunstancia. "
    "Si una categoría no tiene resultados, simplemente omítela del texto — no la menciones "
    "ni en positivo ni en negativo (evita frases como 'no hay parques cercanos')."
)


class NarrativeGenerator:
    def __init__(self, client, model: str = "gemini-2.5-flash"):
        self._client = client
        self._model = model

    def generate(self, report_data: dict) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=json.dumps(report_data, ensure_ascii=False),
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                max_output_tokens=400,
            ),
        )
        return response.text


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
        "transporte", "transporte publico", "parada", "paradas",
        "estacion de transporte", "estaciones de transporte",
        "estacion de metro", "estaciones de metro", "estacion del metro", "estaciones del metro",
        "linea de metro", "lineas de metro", "paradero", "paraderos", "transmilenio",
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

_PRICE_KEYWORDS = [
    "precio", "precios", "valor", "valores", "valorizacion", "valorizaciones",
    "valoriza", "valorizar", "valorizado", "valorizados",
    "avaluo", "avaluos", "costo", "costos", "millon", "millones",
    "cotiza", "cotizacion", "cotizaciones", "arriendo", "arriendos",
    "canon", "canones", "pesos", "cop", "uvr", "smmlv",
]

_PRICE_SYMBOLS = ["$", "%", "m2"]


def _contains_word(text_normalized: str, phrase: str) -> bool:
    return re.search(r"\b" + re.escape(phrase) + r"\b", text_normalized) is not None


def verify_groundedness(text: str, report_data: dict) -> bool:
    """
    Heuristic, category-presence-only groundedness check for the AI-written
    narrative.

    Text is "ungrounded" if:
    1. Any price/valuation-related word or symbol appears at all —
       report_data never contains price data in this version, so any such
       mention is necessarily fabricated.
    2. A category-related keyword appears while that category has zero
       POIs in report_data.

    This check does NOT special-case negation ("no hay parques cercanos").
    The system prompt instructs the model to omit missing categories
    entirely rather than mention their absence; if the model ignores that
    instruction, this check conservatively rejects the text (a safe
    failure — the narrative gets replaced with a fallback message — rather
    than trying to parse negation, which is unreliable with simple
    heuristics and was found to let real fabrications through when a
    negated mention of one category preceded a fabricated mention of
    another in the same sentence).

    Known limitations (accepted, not bugs):
    - Category-presence matching, not entity verification: if a category
      has at least one real POI, this check cannot detect an invented NAME
      for a different place in that category.
    - Bare "café"/"cafés" and bare "estación" are intentionally excluded
      from keywords (color/coffee and "estación de servicio" gas-station
      ambiguity); "cafetería" and specific transit-station phrases are
      used instead, so an honest restaurantes/transporte mention using
      only the ambiguous bare word, if fabricated, may not be caught.
    - "m²" normalizes to "m2" and is treated as a price/measurement
      signal; a legitimate area mention (e.g. "80 m² de área construida")
      will also be rejected. Conservative by design, since report_data
      doesn't carry area data either.
    """
    pois = report_data.get("pois", {})
    text_normalized = _normalize(text)

    for symbol in _PRICE_SYMBOLS:
        if symbol in text_normalized:
            return False
    for price_keyword in _PRICE_KEYWORDS:
        if _contains_word(text_normalized, _normalize(price_keyword)):
            return False

    for category, keywords in _CATEGORY_KEYWORDS.items():
        has_data = len(pois.get(category, [])) > 0
        if has_data:
            continue
        for keyword in keywords:
            if _contains_word(text_normalized, _normalize(keyword)):
                return False

    return True
