"""
Azure Functions v2 Programming Model Entrypoint.
Expone endpoints HTTP y herramientas para agentes de Inteligencia Artificial (MCP/RAG).
Implementa el patrón CQRS para validación documental SUNAT.
"""
import json
import logging
import base64
import azure.functions as func

from src.domain.models import ResultadoValidacion
from src.application.bus import mediator
from src.application.queries import (
    ValidateFichaRucQuery,
    GetFichaRucByDniQuery
)
from src.application.commands import (
    IndexFichaRucCommand,
    UploadBlobCommand
)
from src.crosscutting.constants import (
    RESULTADO_NO_ENCONTRADO,
    MSG_NO_ENCONTRADO,
    KEY_RESULTADO,
    KEY_COMENTARIO,
    HEADER_VALIDATION_RESULT,
    CONTENT_TYPE_PDF,
    TOOL_VALIDAR_DOCUMENTO,
    TOOL_CONSULTAR_FICHA,
)
from src.infrastructure.azure_search_service import AzureSearchService
from src.infrastructure.azure_blob_service import AzureBlobService
from src.infrastructure.openai_extractor_service import OpenAIExtractorService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-azf-rag")

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Verifica el estado del servicio y conectividad con Azure AI Search y Blob Storage."""
    status: dict = {
        "status": "healthy",
        "service": "mcp-azf-rag",
        "azure_search": "unknown",
        "blob_storage": "unknown"
    }
    try:
        search_svc = AzureSearchService()
        search_svc.search_client.get_document_count()
        status["azure_search"] = "connected"
    except Exception as e:
        status["azure_search"] = f"error: {str(e)}"

    try:
        blob_svc = AzureBlobService()
        blob_svc.container_client.exists()
        status["blob_storage"] = "connected"
    except Exception as e:
        status["blob_storage"] = f"error: {str(e)}"

    return func.HttpResponse(
        body=json.dumps(status, indent=2),
        mimetype="application/json",
        status_code=200
    )


@app.route(route="validate", methods=["GET", "POST"])
def validate_document(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint principal de validación (Query CQRS).
    Input:
      - DNI (obligatorio)
      - nombre_persona (opcional)
      - nombre_comercial (opcional)
      - actividad_economica (opcional)

    Output:
      {
        "RESULTADO": "APROBADO" | "OBSERVADO" | "NO_ENCONTRADO",
        "COMENTARIO": "..."
      }
    """
    dni = req.params.get("dni")
    nombre_persona = req.params.get("nombre_persona")
    nombre_comercial = req.params.get("nombre_comercial")
    actividad_economica = req.params.get("actividad_economica")

    if req.method == "POST":
        try:
            req_body = req.get_json()
            if isinstance(req_body, dict):
                dni = req_body.get("dni", dni)
                nombre_persona = req_body.get("nombre_persona", nombre_persona)
                nombre_comercial = req_body.get("nombre_comercial", nombre_comercial)
                actividad_economica = req_body.get("actividad_economica", actividad_economica)
        except ValueError:
            pass

    if not dni:
        return func.HttpResponse(
            body=json.dumps({
                "error": "El parámetro 'dni' es requerido."
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=400
        )

    # Ejecutar Query a través del Mediador CQRS
    query = ValidateFichaRucQuery(
        dni=dni,
        nombre_persona=nombre_persona,
        nombre_comercial=nombre_comercial,
        actividad_economica=actividad_economica
    )
    result = mediator.query(query)
    output = result.to_output_dict(include_datos=True)

    # Mapeo de códigos de respuesta HTTP según especificación
    # 200: Aprobado / Observado
    # 204: No encontrado (con cabeceras y cuerpo informativo)
    if result.RESULTADO == ResultadoValidacion.NO_ENCONTRADO:
        return func.HttpResponse(
            body=json.dumps(output, ensure_ascii=False, indent=2),
            mimetype="application/json",
            status_code=200,  # Retornamos 200 con el cuerpo JSON exacto para el cliente
            headers={HEADER_VALIDATION_RESULT: RESULTADO_NO_ENCONTRADO}
        )

    return func.HttpResponse(
        body=json.dumps(output, ensure_ascii=False, indent=2),
        mimetype="application/json",
        status_code=200,
        headers={HEADER_VALIDATION_RESULT: result.RESULTADO.value}
    )


def _handle_get_document(dni: str | None) -> func.HttpResponse:
    """Función auxiliar para consultar un documento por DNI."""
    if not dni:
        return func.HttpResponse(
            body=json.dumps({"error": "Parámetro 'dni' requerido."}),
            mimetype="application/json",
            status_code=400
        )

    query = GetFichaRucByDniQuery(dni=dni.strip())
    doc = mediator.query(query)

    if not doc:
        return func.HttpResponse(
            body=json.dumps({
                KEY_RESULTADO: RESULTADO_NO_ENCONTRADO,
                KEY_COMENTARIO: MSG_NO_ENCONTRADO
            }, ensure_ascii=False, indent=2),
            mimetype="application/json",
            status_code=200
        )

    return func.HttpResponse(
        body=json.dumps(doc.model_dump(by_alias=True), ensure_ascii=False, indent=2),
        mimetype="application/json",
        status_code=200
    )


@app.route(route="document/{dni}", methods=["GET"])
def get_document_by_path(req: func.HttpRequest) -> func.HttpResponse:
    """Consulta directa a Azure AI Search por DNI en ruta (GET /api/document/{dni})."""
    dni = req.route_params.get("dni")
    return _handle_get_document(dni)


@app.route(route="document", methods=["GET"])
def get_document_by_query(req: func.HttpRequest) -> func.HttpResponse:
    """Consulta directa a Azure AI Search por DNI en parámetro (GET /api/document?dni=12345678)."""
    dni = req.params.get("dni")
    return _handle_get_document(dni)


@app.route(route="v1/cliente", methods=["GET"])
def get_cliente_alias(req: func.HttpRequest) -> func.HttpResponse:
    """Alias para agentes externos (GET /api/v1/cliente?dni=12345678)."""
    dni = req.params.get("dni")
    return _handle_get_document(dni)


@app.route(route="document", methods=["POST"])
def index_document(req: func.HttpRequest) -> func.HttpResponse:
    """Indexa un documento en Azure AI Search (Command CQRS)."""
    try:
        body = req.get_json()
        doc_id = body.get("id") or f"doc-{body.get('dni')}"
        cmd = IndexFichaRucCommand(
            id=doc_id,
            dni=body["dni"],
            ruc=body["ruc"],
            nombre_persona=body["nombre_persona"],
            nombre_comercial=body["nombre_comercial"],
            actividad_economica=body["actividad_economica"]
        )
        success = mediator.send(cmd)
        return func.HttpResponse(
            body=json.dumps({
                "status": "success" if success else "failed",
                "id": doc_id,
                "dni": body["dni"]
            }),
            mimetype="application/json",
            status_code=201 if success else 500
        )
    except KeyError as e:
        return func.HttpResponse(
            body=json.dumps({"error": f"Campo requerido ausente: {str(e)}"}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="upload", methods=["POST"])
def upload_file(req: func.HttpRequest) -> func.HttpResponse:
    """Sube un documento a Azure Blob Storage (Command CQRS)."""
    try:
        body = req.get_json()
        file_name = body["filename"]
        content_b64 = body["content"]
        content_type = body.get("content_type", CONTENT_TYPE_PDF)
        data = base64.b64decode(content_b64)

        cmd = UploadBlobCommand(
            blob_name=file_name,
            data=data,
            content_type=content_type
        )
        blob_url = mediator.send(cmd)
        return func.HttpResponse(
            body=json.dumps({"status": "success", "url": blob_url}),
            mimetype="application/json",
            status_code=201
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="mcp/tools/call", methods=["POST"])
def mcp_tool_call(req: func.HttpRequest) -> func.HttpResponse:
    """
    Endpoint para invocación directa de herramientas MCP desde Agentes vía HTTP.
    Permite llamadas JSON-RPC o simplificadas:
    {
      "name": "validar_documento_por_dni",
      "arguments": { "dni": "12345678", ... }
    }
    """
    try:
        payload = req.get_json()
        tool_name = payload.get("name")
        args = payload.get("arguments", {})

        if tool_name == TOOL_VALIDAR_DOCUMENTO:
            query = ValidateFichaRucQuery(
                dni=args.get("dni", ""),
                nombre_persona=args.get("nombre_persona"),
                nombre_comercial=args.get("nombre_comercial"),
                actividad_economica=args.get("actividad_economica")
            )
            resp = mediator.query(query)
            return func.HttpResponse(
                body=json.dumps(resp.to_output_dict(include_datos=False), ensure_ascii=False, indent=2),
                mimetype="application/json"
            )

        elif tool_name == TOOL_CONSULTAR_FICHA:
            query = GetFichaRucByDniQuery(dni=args.get("dni", ""))
            doc = mediator.query(query)
            if not doc:
                return func.HttpResponse(
                    body=json.dumps({
                        KEY_RESULTADO: RESULTADO_NO_ENCONTRADO,
                        KEY_COMENTARIO: MSG_NO_ENCONTRADO
                    }, ensure_ascii=False, indent=2),
                    mimetype="application/json"
                )
            return func.HttpResponse(
                body=json.dumps(doc.model_dump(by_alias=True), ensure_ascii=False, indent=2),
                mimetype="application/json"
            )

        return func.HttpResponse(
            body=json.dumps({"error": f"Herramienta '{tool_name}' no encontrada"}),
            mimetype="application/json",
            status_code=404
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="skills/extract-ficha", methods=["POST"])
def extract_ficha_skill(req: func.HttpRequest) -> func.HttpResponse:
    """
    Custom Web API Skill para Azure AI Search Skillset (#Microsoft.Skills.Custom.WebApiSkill).
    Recibe el texto extraído del documento (PDF de Ficha RUC en Blob Storage) y utiliza
    Azure OpenAI (gpt-5.6-luna) para extraer los 5 campos estructurados requeridos:
    - dni
    - ruc
    - nombre_persona
    - nombre_comercial
    - actividad_economica
    """
    try:
        req_body = req.get_json()
        values = req_body.get("values", [])
        if not values:
            return func.HttpResponse(
                body=json.dumps({"values": []}),
                mimetype="application/json",
                status_code=200
            )

        extractor = OpenAIExtractorService()
        response_values = []

        for record in values:
            record_id = record.get("recordId")
            data = record.get("data", {})
            text = data.get("text", "") or data.get("content", "")

            try:
                extracted = extractor.extract_fields(text)
                response_values.append({
                    "recordId": record_id,
                    "data": extracted,
                    "errors": [],
                    "warnings": []
                })
            except Exception as item_err:
                logger.error("Error al procesar recordId %s: %s", record_id, str(item_err))
                response_values.append({
                    "recordId": record_id,
                    "data": {
                        "dni": "",
                        "ruc": "",
                        "nombre_persona": "",
                        "nombre_comercial": "-",
                        "actividad_economica": "-"
                    },
                    "errors": [{"message": str(item_err)}],
                    "warnings": []
                })

        return func.HttpResponse(
            body=json.dumps({"values": response_values}, ensure_ascii=False, indent=2),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error("Error global en Custom Web API Skill: %s", str(e))
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
