import unicodedata
from dataclasses import dataclass
from typing import Optional, List
from ..bus import Query, QueryHandler
from ...domain.models import (
    ResultadoValidacion,
    ValidationResponse,
    FichaRucDocument
)
from ...infrastructure.azure_search_service import AzureSearchService


def _normalize(text: Optional[str]) -> str:
    """Normaliza texto para comparación: mayúsculas, sin tildes y sin espacios redundantes."""
    if not text:
        return ""
    # Quitar tildes / diacríticos
    normalized = unicodedata.normalize('NFKD', text)
    without_accents = ''.join(c for c in normalized if not unicodedata.combining(c))
    # Mayúsculas y compactación de espacios
    return " ".join(without_accents.upper().split())


@dataclass
class ValidateFichaRucQuery(Query):
    dni: str
    nombre_persona: Optional[str] = None
    nombre_comercial: Optional[str] = None
    actividad_economica: Optional[str] = None


class ValidateFichaRucQueryHandler(QueryHandler[ValidateFichaRucQuery, ValidationResponse]):
    def __init__(self, search_service: Optional[AzureSearchService] = None) -> None:
        self.search_service = search_service or AzureSearchService()

    def handle(self, query: ValidateFichaRucQuery) -> ValidationResponse:
        # 1. Búsqueda en Azure AI Search por DNI
        doc: Optional[FichaRucDocument] = self.search_service.search_by_dni(query.dni)

        # 2. Si no existe en la base de conocimientos
        if not doc:
            return ValidationResponse(
                RESULTADO=ResultadoValidacion.NO_ENCONTRADO,
                COMENTARIO="El valor recibido no fue encontrado en la base de conocimientos",
                DATOS=None
            )

        # 3. Comparación de campos recibidos con los encontrados en la base de conocimientos
        observaciones: List[str] = []

        if query.nombre_persona is not None:
            if _normalize(query.nombre_persona) != _normalize(doc.nombre_persona):
                observaciones.append("- Campo NOMBRE PERSONA no coincide con el valor")

        if query.nombre_comercial is not None:
            if _normalize(query.nombre_comercial) != _normalize(doc.nombre_comercial):
                observaciones.append("- Campo NOMBRE COMERCIAL no coincide con el valor")

        if query.actividad_economica is not None:
            if _normalize(query.actividad_economica) != _normalize(doc.actividad_economica):
                observaciones.append("- Campo ACTIVIDAD ECONOMICA no coincide con el valor")

        # 4. Evaluación de observaciones
        if observaciones:
            return ValidationResponse(
                RESULTADO=ResultadoValidacion.OBSERVADO,
                COMENTARIO="\n".join(observaciones),
                DATOS=doc.model_dump(by_alias=True)
            )

        # 5. Todo coincide correctamente
        return ValidationResponse(
            RESULTADO=ResultadoValidacion.APROBADO,
            COMENTARIO="Se valida correctamente el contenido",
            DATOS=doc.model_dump(by_alias=True)
        )
