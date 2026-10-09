from .bus import (
    CQRSMediator,
    Command,
    Query,
    CommandHandler,
    QueryHandler,
    mediator
)
from .queries import (
    GetFichaRucByDniQuery,
    GetFichaRucByDniQueryHandler,
    ValidateFichaRucQuery,
    ValidateFichaRucQueryHandler
)
from .commands import (
    UploadBlobCommand,
    UploadBlobCommandHandler,
    IndexFichaRucCommand,
    IndexFichaRucCommandHandler
)
from ..infrastructure.azure_search_service import AzureSearchService
from ..infrastructure.azure_blob_service import AzureBlobService


def setup_mediator(
    search_service: AzureSearchService | None = None,
    blob_service: AzureBlobService | None = None,
    custom_mediator: CQRSMediator | None = None
) -> CQRSMediator:
    """Configura y registra los Command y Query Handlers en el mediador CQRS."""
    target = custom_mediator or mediator
    search_svc = search_service or AzureSearchService()
    blob_svc = blob_service or AzureBlobService()

    # Queries
    target.register_query_handler(GetFichaRucByDniQuery, GetFichaRucByDniQueryHandler(search_svc))
    target.register_query_handler(ValidateFichaRucQuery, ValidateFichaRucQueryHandler(search_svc))

    # Commands
    target.register_command_handler(UploadBlobCommand, UploadBlobCommandHandler(blob_svc))
    target.register_command_handler(IndexFichaRucCommand, IndexFichaRucCommandHandler(search_svc))

    return target


# Registrar por defecto en el mediador global
setup_mediator()

__all__ = [
    "CQRSMediator",
    "Command",
    "Query",
    "CommandHandler",
    "QueryHandler",
    "mediator",
    "setup_mediator",
    "GetFichaRucByDniQuery",
    "ValidateFichaRucQuery",
    "UploadBlobCommand",
    "IndexFichaRucCommand"
]
