import unicodedata
from dataclasses import dataclass
from typing import Optional, List
from ..bus import Query, QueryHandler
from ...domain.models import (
    ResultadoValidacion,
    ValidationResponse,
    FichaRucDocument
)
from ...crosscutting.constants import (
    MSG_APROBADO,
    MSG_NO_ENCONTRADO,
    PLANTILLA_OBSERVACION,
    CAMPO_NOMBRE_PERSONA,
    CAMPO_NOMBRE_COMERCIAL,
    CAMPO_ACTIVIDAD_ECONOMICA,
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
                COMENTARIO=MSG_NO_ENCONTRADO,
                DATOS=None
            )

        # 3. Comparación de campos recibidos con los encontrados en la base de conocimientos
        observaciones: List[str] = []

        if query.nombre_persona is not None:
            if _normalize(query.nombre_persona) != _normalize(doc.nombre_persona):
                observaciones.append(PLANTILLA_OBSERVACION.format(campo=CAMPO_NOMBRE_PERSONA))

        if query.nombre_comercial is not None:
            if _normalize(query.nombre_comercial) != _normalize(doc.nombre_comercial):
                observaciones.append(PLANTILLA_OBSERVACION.format(campo=CAMPO_NOMBRE_COMERCIAL))

        if query.actividad_economica is not None:
            if _normalize(query.actividad_economica) != _normalize(doc.actividad_economica):
                observaciones.append(PLANTILLA_OBSERVACION.format(campo=CAMPO_ACTIVIDAD_ECONOMICA))

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
            COMENTARIO=MSG_APROBADO,
            DATOS=doc.model_dump(by_alias=True)
        )
