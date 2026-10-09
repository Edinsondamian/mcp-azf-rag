from unittest.mock import MagicMock
import pytest
from src.domain.models import ResultadoValidacion, FichaRucDocument
from src.application.queries.validate_ficha_ruc import (
    ValidateFichaRucQuery,
    ValidateFichaRucQueryHandler
)


@pytest.fixture
def sample_document() -> FichaRucDocument:
    return FichaRucDocument(
        id="doc-12345678",
        dni="12345678",
        ruc="10123456781",
        nombre_persona="PEREZ GARCIA JUAN",
        nombre_comercial="JPG IMPORT & EXPORT",
        actividad_economica="4690 - VENTA AL POR MAYOR NO ESPECIALIZADA"
    )


def test_validation_aprobado_all_fields_match(sample_document):
    mock_search = MagicMock()
    mock_search.search_by_dni.return_value = sample_document

    handler = ValidateFichaRucQueryHandler(search_service=mock_search)
    query = ValidateFichaRucQuery(
        dni="12345678",
        nombre_persona="PEREZ GARCIA JUAN",
        nombre_comercial="JPG IMPORT & EXPORT",
        actividad_economica="4690 - VENTA AL POR MAYOR NO ESPECIALIZADA"
    )

    response = handler.handle(query)
    assert response.RESULTADO == ResultadoValidacion.APROBADO
    assert response.COMENTARIO == "Se valida correctamente el contenido"


def test_validation_aprobado_with_case_and_accents_normalization(sample_document):
    mock_search = MagicMock()
    mock_search.search_by_dni.return_value = sample_document

    handler = ValidateFichaRucQueryHandler(search_service=mock_search)
    # Entrada con minúsculas y tildes
    query = ValidateFichaRucQuery(
        dni="12345678",
        nombre_persona="pérez garcía juan",
        nombre_comercial="jpg import & export",
        actividad_economica="4690 - venta al por mayor no especializada"
    )

    response = handler.handle(query)
    assert response.RESULTADO == ResultadoValidacion.APROBADO
    assert response.COMENTARIO == "Se valida correctamente el contenido"


def test_validation_observado_single_field(sample_document):
    mock_search = MagicMock()
    mock_search.search_by_dni.return_value = sample_document

    handler = ValidateFichaRucQueryHandler(search_service=mock_search)
    query = ValidateFichaRucQuery(
        dni="12345678",
        nombre_persona="PEREZ GARCIA JUAN",
        nombre_comercial="EMPRESA EQUIVOCADA",
        actividad_economica="4690 - VENTA AL POR MAYOR NO ESPECIALIZADA"
    )

    response = handler.handle(query)
    assert response.RESULTADO == ResultadoValidacion.OBSERVADO
    assert "- Campo NOMBRE COMERCIAL no coincide con el valor" in response.COMENTARIO


def test_validation_observado_multiple_fields(sample_document):
    mock_search = MagicMock()
    mock_search.search_by_dni.return_value = sample_document

    handler = ValidateFichaRucQueryHandler(search_service=mock_search)
    query = ValidateFichaRucQuery(
        dni="12345678",
        nombre_persona="LOPEZ ALVAREZ CARLOS",
        nombre_comercial="JPG IMPORT & EXPORT",
        actividad_economica="OTRA ACTIVIDAD"
    )

    response = handler.handle(query)
    assert response.RESULTADO == ResultadoValidacion.OBSERVADO
    assert "- Campo NOMBRE PERSONA no coincide con el valor" in response.COMENTARIO
    assert "- Campo ACTIVIDAD ECONOMICA no coincide con el valor" in response.COMENTARIO


def test_validation_no_encontrado():
    mock_search = MagicMock()
    mock_search.search_by_dni.return_value = None

    handler = ValidateFichaRucQueryHandler(search_service=mock_search)
    query = ValidateFichaRucQuery(
        dni="99999999",
        nombre_persona="ALGUIEN"
    )

    response = handler.handle(query)
    assert response.RESULTADO == ResultadoValidacion.NO_ENCONTRADO
    assert response.COMENTARIO == "El valor recibido no fue encontrado en la base de conocimientos"
