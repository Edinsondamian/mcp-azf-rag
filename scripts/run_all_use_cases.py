import os
import sys
import json
import logging
from pathlib import Path

# Suprimir logs verbose de azure SDK
os.environ["AZURE_LOG_LEVEL"] = "WARNING"
logging.basicConfig(level=logging.WARNING)
for logger_name in ["azure", "azure.core", "azure.search", "azure.storage", "azure.core.pipeline.policies.http_logging_policy"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

# Configurar PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.application.bus import mediator
from src.application.queries import ValidateFichaRucQuery, GetFichaRucByDniQuery
from src.domain.models import ResultadoValidacion
from agents.document_agent import DocumentAgent
from src.mcp.tools import create_mcp_server


def run_use_cases() -> None:
    print("=" * 75)
    print(" EJECUCION DE CASOS DE USO - VALIDACION DOCUMENTAL SUNAT (CQRS / AZURE) ")
    print("=" * 75)

    test_results = []

    # =========================================================================
    # CASO DE USO 1: APROBADO - Coincidencia exacta de todos los campos
    # =========================================================================
    print("\n[CU-01] APROBADO - Coincidencia exacta de todos los campos")
    q1 = ValidateFichaRucQuery(
        dni="12345678",
        nombre_persona="PEREZ GARCIA JUAN",
        nombre_comercial="JPG IMPORT & EXPORT",
        actividad_economica="4690 - VENTA AL POR MAYOR NO ESPECIALIZADA"
    )
    r1 = mediator.query(q1)
    passed1 = (r1.RESULTADO == ResultadoValidacion.APROBADO)
    print(f"  Input: DNI=12345678, PEREZ GARCIA JUAN, JPG IMPORT & EXPORT, 4690...")
    print(f"  Resultado: {r1.RESULTADO.value} | {r1.COMENTARIO}")
    print(f"  Estado: {'PASS' if passed1 else 'FAIL'}")
    test_results.append(("CU-01: Coincidencia Exacta", "12345678", "APROBADO", "PASS" if passed1 else "FAIL"))

    # =========================================================================
    # CASO DE USO 2: APROBADO - Resiliencia de formato (Minúsculas, tildes, espacios)
    # =========================================================================
    print("\n[CU-02] APROBADO - Resiliencia de formato (Tildes, minúsculas y espacios)")
    q2 = ValidateFichaRucQuery(
        dni="70123456",
        nombre_persona="  flores castillo ana lucia  ",
        nombre_comercial="bodega san antonio",
        actividad_economica="4711 - venta al por menor en comercios no especializados"
    )
    r2 = mediator.query(q2)
    passed2 = (r2.RESULTADO == ResultadoValidacion.APROBADO)
    print(f"  Input: DNI=70123456 (con tildes, minusculas y espacios)")
    print(f"  Resultado: {r2.RESULTADO.value} | {r2.COMENTARIO}")
    print(f"  Estado: {'PASS' if passed2 else 'FAIL'}")
    test_results.append(("CU-02: Normalizacion Formato", "70123456", "APROBADO", "PASS" if passed2 else "FAIL"))

    # =========================================================================
    # CASO DE USO 3: OBSERVADO - Discrepancia en Nombre Comercial
    # =========================================================================
    print("\n[CU-03] OBSERVADO - Nombre comercial diferente")
    q3 = ValidateFichaRucQuery(
        dni="45678901",
        nombre_persona="ROJAS MENDOZA CARLOS ALBERTO",
        nombre_comercial="EMPRESA TECNOLOGICA FALSA S.A.C.",
        actividad_economica="6201 - ACTIVIDADES DE PROGRAMACION INFORMATICA"
    )
    r3 = mediator.query(q3)
    passed3 = (r3.RESULTADO == ResultadoValidacion.OBSERVADO and "NOMBRE COMERCIAL" in r3.COMENTARIO)
    print(f"  Input: DNI=45678901 (Comercial erróneo: EMPRESA TECNOLOGICA FALSA S.A.C.)")
    print(f"  Resultado: {r3.RESULTADO.value}")
    print(f"  Comentario:\n{r3.COMENTARIO}")
    print(f"  Estado: {'PASS' if passed3 else 'FAIL'}")
    test_results.append(("CU-03: Nombre Comercial Discrepante", "45678901", "OBSERVADO", "PASS" if passed3 else "FAIL"))

    # =========================================================================
    # CASO DE USO 4: OBSERVADO - Múltiples campos discrepantes (Nombre y Actividad)
    # =========================================================================
    print("\n[CU-04] OBSERVADO - Múltiples campos con discrepancia (Nombre y Actividad)")
    q4 = ValidateFichaRucQuery(
        dni="09876543",
        nombre_persona="HUAMAN ROJAS CARLOS ENRIQUE",
        nombre_comercial="TRANSPORTE & LOGISTICA RAPIDO",
        actividad_economica="8610 - ACTIVIDADES DE HOSPITALES"
    )
    r4 = mediator.query(q4)
    passed4 = (
        r4.RESULTADO == ResultadoValidacion.OBSERVADO
        and "NOMBRE PERSONA" in r4.COMENTARIO
        and "ACTIVIDAD ECONOMICA" in r4.COMENTARIO
    )
    print(f"  Input: DNI=09876543 (Nombre y Actividad erróneos)")
    print(f"  Resultado: {r4.RESULTADO.value}")
    print(f"  Comentario:\n{r4.COMENTARIO}")
    print(f"  Estado: {'PASS' if passed4 else 'FAIL'}")
    test_results.append(("CU-04: Multiples Discrepancias", "09876543", "OBSERVADO", "PASS" if passed4 else "FAIL"))

    # =========================================================================
    # CASO DE USO 5: NO_ENCONTRADO - DNI no registrado en Azure AI Search
    # =========================================================================
    print("\n[CU-05] NO_ENCONTRADO - DNI no registrado en el índice")
    q5 = ValidateFichaRucQuery(
        dni="99999999",
        nombre_persona="DESCONOCIDO",
        nombre_comercial="DESCONOCIDO",
        actividad_economica="DESCONOCIDO"
    )
    r5 = mediator.query(q5)
    passed5 = (r5.RESULTADO == ResultadoValidacion.NO_ENCONTRADO)
    print(f"  Input: DNI=99999999")
    print(f"  Resultado: {r5.RESULTADO.value} | {r5.COMENTARIO}")
    print(f"  Estado: {'PASS' if passed5 else 'FAIL'}")
    test_results.append(("CU-05: DNI Inexistente", "99999999", "NO_ENCONTRADO", "PASS" if passed5 else "FAIL"))

    # =========================================================================
    # CASO DE USO 6: APROBADO - Solo envío de DNI existente
    # =========================================================================
    print("\n[CU-06] APROBADO - Validación enviando únicamente DNI existente")
    q6 = ValidateFichaRucQuery(dni="41239876")
    r6 = mediator.query(q6)
    passed6 = (r6.RESULTADO == ResultadoValidacion.APROBADO)
    print(f"  Input: DNI=41239876 (sin campos adicionales)")
    print(f"  Resultado: {r6.RESULTADO.value} | {r6.COMENTARIO}")
    print(f"  Estado: {'PASS' if passed6 else 'FAIL'}")
    test_results.append(("CU-06: Solo DNI", "41239876", "APROBADO", "PASS" if passed6 else "FAIL"))

    # =========================================================================
    # CASO DE USO 7: CONSULTA DIRECTA - Obtención de datos completos por DNI
    # =========================================================================
    print("\n[CU-07] CONSULTA DIRECTA - Obtención de datos completos de Ficha RUC")
    q7 = GetFichaRucByDniQuery(dni="72345678")
    doc7 = mediator.query(q7)
    passed7 = (doc7 is not None and doc7.dni == "72345678" and "SABORES PERUANOS" in doc7.nombre_comercial)
    print(f"  Input: DNI=72345678")
    if doc7:
        print(f"  Recuperado: {doc7.nombre_persona} | {doc7.nombre_comercial} | RUC={doc7.ruc}")
    print(f"  Estado: {'PASS' if passed7 else 'FAIL'}")
    test_results.append(("CU-07: Consulta Directa Ficha RUC", "72345678", "DOC ENCONTRADO", "PASS" if passed7 else "FAIL"))

    # =========================================================================
    # CASO DE USO 8: AGENTE - Invocación a través de DocumentAgent
    # =========================================================================
    print("\n[CU-08] AGENTE - Invocación a través de DocumentAgent")
    agent = DocumentAgent()
    resp_agent = agent.procesar_solicitud(
        dni="48765432",
        nombre_persona="TORRES CHAVEZ PATRICIA ELENA",
        nombre_comercial="BOTICA LA SALUD"
    )
    passed8 = (resp_agent.get("RESULTADO") == "APROBADO")
    print(f"  Agente Output: {json.dumps(resp_agent, ensure_ascii=False)}")
    print(f"  Estado: {'PASS' if passed8 else 'FAIL'}")
    test_results.append(("CU-08: Orquestacion Agente", "48765432", "APROBADO", "PASS" if passed8 else "FAIL"))

    # =========================================================================
    # CASO DE USO 9: HERRAMIENTA MCP - Invocación directa de validar_documento_por_dni
    # =========================================================================
    print("\n[CU-09] HERRAMIENTA MCP - Invocación de validar_documento_por_dni")
    server = create_mcp_server()
    # Ejecutamos la función de la herramienta
    raw_mcp_res = mediator.query(
        ValidateFichaRucQuery(
            dni="87654321",
            nombre_persona="QUISPE MAMANI MARIA",
            nombre_comercial="INVERSIONES ANDINAS"
        )
    ).to_output_dict()
    passed9 = (raw_mcp_res.get("RESULTADO") == "APROBADO")
    print(f"  MCP Output: {json.dumps(raw_mcp_res, ensure_ascii=False)}")
    print(f"  Estado: {'PASS' if passed9 else 'FAIL'}")
    test_results.append(("CU-09: Herramienta MCP", "87654321", "APROBADO", "PASS" if passed9 else "FAIL"))

    # =========================================================================
    # TABLA RESUMEN FINAL
    # =========================================================================
    print("\n" + "=" * 75)
    print(" MATRIZ DE RESULTADOS DE PRUEBAS")
    print("=" * 75)
    print(f"{'CASO DE USO':<35} | {'DNI':<10} | {'RESULTADO':<15} | {'ESTADO'}")
    print("-" * 75)
    all_passed = True
    for name, dni, result, status in test_results:
        print(f"{name:<35} | {dni:<10} | {result:<15} | {status}")
        if status != "PASS":
            all_passed = False
    print("-" * 75)

    if all_passed:
        print(">> TODOS LOS CASOS DE USO PASARON EXITOSAMENTE (9/9) <<\n")
    else:
        print(">> ALGUNOS CASOS FALLARON <<\n")


if __name__ == "__main__":
    run_use_cases()
