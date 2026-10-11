"""
Script de automatización para configurar el Pipeline de Ingesta Inteligente en Azure AI Search:
1. Data Source: Conecta el contenedor 'namerag-poc' en Blob Storage
2. Skillset: Custom Web API Skill que invoca la Azure Function / LLM (gpt-5.6-luna)
3. Indexer: Conecta Data Source -> Skillset -> 'fichas-ruc-index'
"""
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings
from src.crosscutting.constants import (
    DEFAULT_INDEX_NAME,
    DEFAULT_CONTAINER_NAME,
    DEFAULT_DATASOURCE_NAME,
    DEFAULT_SKILLSET_NAME,
    DEFAULT_INDEXER_NAME,
)

FUNCTION_URL = "https://azf-mcp-tools-poc-aeengrd7hmcuhrbf.brazilsouth-01.azurewebsites.net/api/skills/extract-ficha"


def _send_request(url: str, method: str, payload: dict | None = None) -> dict:
    headers = {
        "Content-Type": "application/json",
        "api-key": settings.AZURE_SEARCH_API_KEY
    }
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        print(f"[-] Error HTTP {e.code} en {method} {url}:\n{err_msg}")
        raise


def setup_data_source() -> None:
    print(f"\n[1/3] Configurando Data Source: {DEFAULT_DATASOURCE_NAME}...")
    url = f"{settings.AZURE_SEARCH_ENDPOINT}/datasources/{DEFAULT_DATASOURCE_NAME}?api-version=2024-07-01"
    payload = {
        "name": DEFAULT_DATASOURCE_NAME,
        "type": "azureblob",
        "credentials": {
            "connectionString": settings.AZURE_STORAGE_CONNECTION_STRING
        },
        "container": {
            "name": DEFAULT_CONTAINER_NAME
        },
        "description": "Origen de datos conectado al contenedor de PDFs namerag-poc"
    }
    _send_request(url, "PUT", payload)
    print(f"  [OK] Data Source '{DEFAULT_DATASOURCE_NAME}' configurado.")


def setup_skillset() -> None:
    print(f"\n[2/3] Configurando Skillset: {DEFAULT_SKILLSET_NAME}...")
    url = f"{settings.AZURE_SEARCH_ENDPOINT}/skillsets/{DEFAULT_SKILLSET_NAME}?api-version=2024-07-01"
    payload = {
        "name": DEFAULT_SKILLSET_NAME,
        "description": "Skillset para extracción estructurada de Fichas RUC SUNAT usando gpt-5.6-luna",
        "skills": [
            {
                "@odata.type": "#Microsoft.Skills.Custom.WebApiSkill",
                "name": "extract-ficha-ruc-skill",
                "description": "Extrae dni, ruc, nombre_persona, nombre_comercial y actividad_economica",
                "uri": FUNCTION_URL,
                "httpMethod": "POST",
                "timeout": "PT230S",
                "batchSize": 1,
                "inputs": [
                    {
                        "name": "text",
                        "source": "/document/content"
                    }
                ],
                "outputs": [
                    {"name": "dni", "targetName": "dni"},
                    {"name": "ruc", "targetName": "ruc"},
                    {"name": "nombre_persona", "targetName": "nombre_persona"},
                    {"name": "nombre_comercial", "targetName": "nombre_comercial"},
                    {"name": "actividad_economica", "targetName": "actividad_economica"}
                ]
            }
        ]
    }
    _send_request(url, "PUT", payload)
    print(f"  [OK] Skillset '{DEFAULT_SKILLSET_NAME}' configurado.")


def setup_indexer() -> None:
    print(f"\n[3/3] Configurando Indexer: {DEFAULT_INDEXER_NAME}...")
    url = f"{settings.AZURE_SEARCH_ENDPOINT}/indexers/{DEFAULT_INDEXER_NAME}?api-version=2024-07-01"
    payload = {
        "name": DEFAULT_INDEXER_NAME,
        "dataSourceName": DEFAULT_DATASOURCE_NAME,
        "targetIndexName": DEFAULT_INDEX_NAME,
        "skillsetName": DEFAULT_SKILLSET_NAME,
        "description": "Indexador que procesa PDFs desde namerag-poc hacia fichas-ruc-index",
        "parameters": {
            "configuration": {
                "dataToExtract": "contentAndMetadata",
                "parsingMode": "default"
            }
        },
        "fieldMappings": [
            {
                "sourceFieldName": "metadata_storage_path",
                "targetFieldName": "id",
                "mappingFunction": {
                    "name": "base64Encode"
                }
            }
        ],
        "outputFieldMappings": [
            {"sourceFieldName": "/document/dni", "targetFieldName": "dni"},
            {"sourceFieldName": "/document/ruc", "targetFieldName": "ruc"},
            {"sourceFieldName": "/document/nombre_persona", "targetFieldName": "nombre_persona"},
            {"sourceFieldName": "/document/nombre_comercial", "targetFieldName": "nombre_comercial"},
            {"sourceFieldName": "/document/actividad_economica", "targetFieldName": "actividad_economica"}
        ]
    }
    _send_request(url, "PUT", payload)
    print(f"  [OK] Indexer '{DEFAULT_INDEXER_NAME}' configurado.")


def main():
    print("=================================================================")
    print(" CONFIGURANDO PIPELINE DE AZURE AI SEARCH (SKILLSET + INDEXER)  ")
    print("=================================================================")
    setup_data_source()
    setup_skillset()
    setup_indexer()
    print("\n[ÉXITO] Todo el pipeline cognitivo ha sido configurado en Azure AI Search.")


if __name__ == "__main__":
    main()
