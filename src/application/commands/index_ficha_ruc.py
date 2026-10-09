from dataclasses import dataclass
from typing import Optional
from ..bus import Command, CommandHandler
from ...domain.models import FichaRucDocument
from ...infrastructure.azure_search_service import AzureSearchService


@dataclass
class IndexFichaRucCommand(Command):
    id: str
    dni: str
    ruc: str
    nombre_persona: str
    nombre_comercial: str
    actividad_economica: str


class IndexFichaRucCommandHandler(CommandHandler[IndexFichaRucCommand, bool]):
    def __init__(self, search_service: Optional[AzureSearchService] = None) -> None:
        self.search_service = search_service or AzureSearchService()

    def handle(self, command: IndexFichaRucCommand) -> bool:
        doc = FichaRucDocument(
            id=command.id,
            dni=command.dni,
            ruc=command.ruc,
            nombre_persona=command.nombre_persona,
            nombre_comercial=command.nombre_comercial,
            actividad_economica=command.actividad_economica
        )
        return self.search_service.index_document(doc)
