"""
Script interactivo para probar las consultas CQRS sobre Azure AI Search.
Prueba los 3 escenarios:
 1. APROBADO (Todos los campos coinciden)
 2. OBSERVADO (Campos con diferencias)
 3. NO_ENCONTRADO (DNI no registrado)
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.application.bus import mediator
from src.application.queries import ValidateFichaRucQuery, GetFichaRucByDniQuery


def run_tests() -> None:
    print("==================================================")
    print(" PRUEBAS DE VALIDACION CQRS (AZURE AI SEARCH) ")
    print("==================================================\n")

    # Caso 1: APROBADO
    print("--- CASO 1: APROBADO ---")
    q1 = ValidateFichaRucQuery(
        dni="12345678",
        nombre_persona="PEREZ GARCIA JUAN",
        nombre_comercial="JPG IMPORT & EXPORT",
        actividad_economica="4690 - VENTA AL POR MAYOR NO ESPECIALIZADA"
    )
    res1 = mediator.query(q1)
    print(json.dumps(res1.to_output_dict(), ensure_ascii=False, indent=2))
    print()

    # Caso 2: OBSERVADO (Nombre comercial y actividad erróneos)
    print("--- CASO 2: OBSERVADO ---")
    q2 = ValidateFichaRucQuery(
        dni="12345678",
        nombre_persona="PEREZ GARCIA JUAN",
        nombre_comercial="OTRA EMPRESA S.A.C.",
        actividad_economica="8610 - ACTIVIDADES DE HOSPITALES"
    )
    res2 = mediator.query(q2)
    print(json.dumps(res2.to_output_dict(), ensure_ascii=False, indent=2))
    print()

    # Caso 3: NO ENCONTRADO
    print("--- CASO 3: NO_ENCONTRADO ---")
    q3 = ValidateFichaRucQuery(
        dni="99999999",
        nombre_persona="NO EXISTE",
        nombre_comercial="NO EXISTE",
        actividad_economica="NO EXISTE"
    )
    res3 = mediator.query(q3)
    print(json.dumps(res3.to_output_dict(), ensure_ascii=False, indent=2))
    print()

    # Caso 4: Consulta directa por DNI
    print("--- CASO 4: CONSULTA DIRECTA DE DOCUMENTO ---")
    q4 = GetFichaRucByDniQuery(dni="12345678")
    doc = mediator.query(q4)
    if doc:
        print(json.dumps(doc.model_dump(by_alias=True), ensure_ascii=False, indent=2))
    else:
        print("Documento no encontrado.")


if __name__ == "__main__":
    run_tests()
