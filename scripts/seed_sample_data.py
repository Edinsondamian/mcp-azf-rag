"""
Script para sembrar datos de prueba en Azure AI Search (fichas-ruc-index)
y Azure Blob Storage (namerag-poc).
"""
import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.application.bus import mediator
from src.application.commands import IndexFichaRucCommand, UploadBlobCommand
from src.infrastructure.azure_search_service import AzureSearchService
from src.infrastructure.azure_blob_service import AzureBlobService


def seed() -> None:
    print("=== Inicializando recursos de Azure ===")
    search_svc = AzureSearchService()
    search_svc.ensure_index_exists()

    blob_svc = AzureBlobService()
    blob_svc.ensure_container_exists()

    # 1. Sembrar documento de ejemplo (del prompt del usuario)
    print("\n1. Indexando documento de prueba en 'fichas-ruc-index'...")
    cmd1 = IndexFichaRucCommand(
        id="doc-12345678",
        dni="12345678",
        ruc="10123456781",
        nombre_persona="PEREZ GARCIA JUAN",
        nombre_comercial="JPG IMPORT & EXPORT",
        actividad_economica="4690 - VENTA AL POR MAYOR NO ESPECIALIZADA"
    )
    res1 = mediator.send(cmd1)
    print(f"Documento DNI 12345678 indexado: {res1}")

    # 2. Sembrar un segundo documento
    cmd2 = IndexFichaRucCommand(
        id="doc-87654321",
        dni="87654321",
        ruc="10876543212",
        nombre_persona="QUISPE MAMANI MARIA",
        nombre_comercial="INVERSIONES ANDINAS",
        actividad_economica="4711 - VENTA AL POR MENOR EN COMERCIOS NO ESPECIALIZADOS"
    )
    res2 = mediator.send(cmd2)
    print(f"Documento DNI 87654321 indexado: {res2}")

    # 3. Subir un archivo de prueba a Blob Storage
    print("\n2. Subiendo documento de prueba a Blob Storage...")
    sample_content = b"%PDF-1.4 Ficha RUC simulada para DNI 12345678 SUNAT"
    cmd_blob = UploadBlobCommand(
        blob_name="fichas/ficha_ruc_12345678.pdf",
        data=sample_content,
        content_type="application/pdf"
    )
    blob_url = mediator.send(cmd_blob)
    print(f"Blob subido exitosamente a: {blob_url}")

    print("\nDatos sembrados correctamente.")


if __name__ == "__main__":
    seed()
