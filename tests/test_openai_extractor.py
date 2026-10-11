"""
Pruebas unitarias para el servicio de extracción OpenAIExtractorService.
"""
from unittest.mock import patch, MagicMock
import json
import pytest

from src.infrastructure.openai_extractor_service import OpenAIExtractorService


def test_openai_extractor_empty_text():
    svc = OpenAIExtractorService()
    res = svc.extract_fields("")
    assert res["dni"] == ""
    assert res["ruc"] == ""
    assert res["nombre_comercial"] == "-"


@patch("urllib.request.urlopen")
def test_openai_extractor_success(mock_urlopen):
    mock_response = MagicMock()
    mock_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "dni": "12345678",
                        "ruc": "10123456781",
                        "nombre_persona": "PEREZ GARCIA JUAN",
                        "nombre_comercial": "JPG IMPORT",
                        "actividad_economica": "4690 - VENTA AL POR MAYOR"
                    })
                }
            }
        ]
    }
    mock_response.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    svc = OpenAIExtractorService(
        endpoint="https://fake.openai.azure.com",
        api_key="fake-key",
        deployment="gpt-5.6-luna"
    )
    result = svc.extract_fields("Texto de prueba")

    assert result["dni"] == "12345678"
    assert result["ruc"] == "10123456781"
    assert result["nombre_persona"] == "PEREZ GARCIA JUAN"
    assert result["nombre_comercial"] == "JPG IMPORT"
    assert result["actividad_economica"] == "4690 - VENTA AL POR MAYOR"
