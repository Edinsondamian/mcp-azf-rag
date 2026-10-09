from typing import Optional
from dataclasses import dataclass
from ..bus import Query, QueryHandler
from ...domain.models import FichaRucDocument
from ...infrastructure.azure_search_service import AzureSearchService


@dataclass
class GetFichaRucByDniQuery(Query):
    dni: str


class GetFichaRucByDniQueryHandler(QueryHandler[GetFichaRucByDniQuery, Optional[FichaRucDocument]]):
    def __init__(self, search_service: Optional[AzureSearchService] = None) -> None:
        self.search_service = search_service or AzureSearchService()

    def handle(self, query: GetFichaRucByDniQuery) -> Optional[FichaRucDocument]:
        return self.search_service.search_by_dni(query.dni)
