from unittest.mock import MagicMock
from src.application.bus import CQRSMediator
from src.application.queries import (
    GetFichaRucByDniQuery,
    GetFichaRucByDniQueryHandler
)
from src.application.commands import (
    IndexFichaRucCommand,
    IndexFichaRucCommandHandler,
    UploadBlobCommand,
    UploadBlobCommandHandler
)
from src.domain.models import FichaRucDocument


def test_cqrs_query_flow():
    mock_search = MagicMock()
    mock_search.search_by_dni.return_value = FichaRucDocument(
        id="doc-12345678",
        dni="12345678",
        ruc="10123456781",
        nombre_persona="PEREZ JUAN",
        nombre_comercial="JPG",
        actividad_economica="VENTAS"
    )

    mediator = CQRSMediator()
    mediator.register_query_handler(GetFichaRucByDniQuery, GetFichaRucByDniQueryHandler(mock_search))

    query = GetFichaRucByDniQuery(dni="12345678")
    result = mediator.query(query)

    assert result is not None
    assert result.dni == "12345678"
    assert result.nombre_persona == "PEREZ JUAN"
    mock_search.search_by_dni.assert_called_once_with("12345678")


def test_cqrs_command_index_flow():
    mock_search = MagicMock()
    mock_search.index_document.return_value = True

    mediator = CQRSMediator()
    mediator.register_command_handler(IndexFichaRucCommand, IndexFichaRucCommandHandler(mock_search))

    cmd = IndexFichaRucCommand(
        id="doc-1",
        dni="12345678",
        ruc="10123456781",
        nombre_persona="PEREZ JUAN",
        nombre_comercial="JPG",
        actividad_economica="VENTAS"
    )
    success = mediator.send(cmd)

    assert success is True
    mock_search.index_document.assert_called_once()


def test_cqrs_command_upload_blob_flow():
    mock_blob = MagicMock()
    mock_blob.upload_file.return_value = "https://blobagentespoc.blob.core.windows.net/namerag-poc/test.pdf"

    mediator = CQRSMediator()
    mediator.register_command_handler(UploadBlobCommand, UploadBlobCommandHandler(mock_blob))

    cmd = UploadBlobCommand(
        blob_name="test.pdf",
        data=b"dummy pdf bytes"
    )
    url = mediator.send(cmd)

    assert "blobagentespoc" in url
    mock_blob.upload_file.assert_called_once()
