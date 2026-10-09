"""
Script para sembrar datos de prueba en Azure AI Search (fichas-ruc-index)
y Azure Blob Storage (namerag-poc).
Carga múltiples registros realistas para pruebas de la POC.
"""
import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.application.bus import mediator
from src.application.commands import IndexFichaRucCommand, UploadBlobCommand
from src.infrastructure.azure_search_service import AzureSearchService
from src.infrastructure.azure_blob_service import AzureBlobService

# Conjunto de datos de prueba para la POC
MOCK_FICHAS_RUC = [
    {
        "id": "doc-12345678",
        "dni": "12345678",
        "ruc": "10123456781",
        "nombre_persona": "PEREZ GARCIA JUAN",
        "nombre_comercial": "JPG IMPORT & EXPORT",
        "actividad_economica": "4690 - VENTA AL POR MAYOR NO ESPECIALIZADA"
    },
    {
        "id": "doc-87654321",
        "dni": "87654321",
        "ruc": "10876543212",
        "nombre_persona": "QUISPE MAMANI MARIA",
        "nombre_comercial": "INVERSIONES ANDINAS",
        "actividad_economica": "4711 - VENTA AL POR MENOR EN COMERCIOS NO ESPECIALIZADOS"
    },
    {
        "id": "doc-45678901",
        "dni": "45678901",
        "ruc": "10456789013",
        "nombre_persona": "ROJAS MENDOZA CARLOS ALBERTO",
        "nombre_comercial": "SOLUCIONES DIGITALES DEL SUR",
        "actividad_economica": "6201 - ACTIVIDADES DE PROGRAMACION INFORMATICA"
    },
    {
        "id": "doc-70123456",
        "dni": "70123456",
        "ruc": "10701234564",
        "nombre_persona": "FLORES CASTILLO ANA LUCIA",
        "nombre_comercial": "BODEGA SAN ANTONIO",
        "actividad_economica": "4711 - VENTA AL POR MENOR EN COMERCIOS NO ESPECIALIZADOS"
    },
    {
        "id": "doc-09876543",
        "dni": "09876543",
        "ruc": "10098765435",
        "nombre_persona": "HUAMAN CONDORI CESAR AUGUSTO",
        "nombre_comercial": "TRANSPORTE & LOGISTICA RAPIDO",
        "actividad_economica": "4923 - TRANSPORTE DE CARGA POR CARRETERA"
    },
    {
        "id": "doc-41239876",
        "dni": "41239876",
        "ruc": "10412398766",
        "nombre_persona": "VEGA SANDOVAL ROSA ELVIRA",
        "nombre_comercial": "CONSULTORIA CONTABLE VEGA",
        "actividad_economica": "6920 - ACTIVIDADES DE CONTABILIDAD, TENEDURIA DE LIBROS Y AUDITORIA"
    },
    {
        "id": "doc-72345678",
        "dni": "72345678",
        "ruc": "10723456787",
        "nombre_persona": "GOMEZ VARGAS JORGE LUIS",
        "nombre_comercial": "RESTAURANTE SABORES PERUANOS",
        "actividad_economica": "5610 - ACTIVIDADES DE RESTAURANTES Y DE SERVICIO MOVIL DE COMIDAS"
    },
    {
        "id": "doc-48765432",
        "dni": "48765432",
        "ruc": "10487654328",
        "nombre_persona": "TORRES CHAVEZ PATRICIA ELENA",
        "nombre_comercial": "BOTICA LA SALUD",
        "actividad_economica": "4772 - VENTA AL POR MENOR DE PRODUCTOS FARMACEUTICOS Y MEDICINALES"
    }
]


def seed() -> None:
    print("==========================================================")
    print(" SEEDER: POBLANDO DATOS DE PRUEBA EN AZURE (POC) ")
    print("==========================================================")

    search_svc = AzureSearchService()
    search_svc.ensure_index_exists()

    blob_svc = AzureBlobService()
    blob_svc.ensure_container_exists()

    # 1. Indexar registros en Azure AI Search
    print(f"\n1. Indexando {len(MOCK_FICHAS_RUC)} contribuyentes en 'fichas-ruc-index'...")
    for item in MOCK_FICHAS_RUC:
        cmd = IndexFichaRucCommand(
            id=item["id"],
            dni=item["dni"],
            ruc=item["ruc"],
            nombre_persona=item["nombre_persona"],
            nombre_comercial=item["nombre_comercial"],
            actividad_economica=item["actividad_economica"]
        )
        res = mediator.send(cmd)
        status = "OK" if res else "FALLO"
        print(f"   [{status}] DNI: {item['dni']} | RUC: {item['ruc']} | {item['nombre_persona']}")

    # 2. Subir PDFs de prueba representativos a Blob Storage
    print("\n2. Subiendo documentos de prueba representativos a Blob Storage...")
    for item in MOCK_FICHAS_RUC[:3]:
        sample_content = (
            f"%PDF-1.4 Ficha RUC SUNAT\n"
            f"DNI: {item['dni']}\nRUC: {item['ruc']}\n"
            f"Persona: {item['nombre_persona']}\n"
            f"Comercial: {item['nombre_comercial']}\n"
            f"Actividad: {item['actividad_economica']}\n"
        ).encode("utf-8")

        cmd_blob = UploadBlobCommand(
            blob_name=f"fichas/ficha_ruc_{item['dni']}.pdf",
            data=sample_content,
            content_type="application/pdf"
        )
        blob_url = mediator.send(cmd_blob)
        print(f"   [BLOB OK] {item['dni']} -> {blob_url}")

    print("\n[EXITO] Todos los datos han sido sembrados exitosamente en Azure.")


if __name__ == "__main__":
    seed()
