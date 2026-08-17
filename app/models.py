from enum import Enum
from pydantic import BaseModel


class Coordinates(BaseModel):
    lat: float
    lon: float


class Categoria(str, Enum):
    EDUCACION = "educacion"
    SALUD = "salud"
    TRANSPORTE = "transporte"
    COMERCIO = "comercio"
    RESTAURANTES = "restaurantes"
    PARQUES = "parques"
    BANCOS = "bancos"


class POI(BaseModel):
    name: str
    category: Categoria
    lat: float
    lon: float
    distance_m: float


class Isochrone(BaseModel):
    minutes: int
    geojson: dict


class SubScore(BaseModel):
    name: str
    value: float
    explanation: str


class ScoreResult(BaseModel):
    sub_scores: list[SubScore]
    global_score: float
