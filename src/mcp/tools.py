import base64
import json
import logging
from typing import Optional, Dict, Any

try:
    from mcp.server.mcpserver import MCPServer
except (ImportError, ModuleNotFoundError):
    try:
        from mcp.server.fastmcp import FastMCP as MCPServer
    except Exception:
        MCPServer = None

from ..application.bus import mediator
from ..application.queries import ValidateFichaRucQuery, GetFichaRucByDniQuery
from ..application.commands import IndexFichaRucCommand, UploadBlobCommand
from ..crosscutting.constants import (
    MCP_SERVER_NAME,
    RESULTADO_NO_ENCONTRADO,
    MSG_NO_ENCONTRADO,
    KEY_RESULTADO,
    KEY_COMENTARIO,
    CONTENT_TYPE_PDF,
)

logger = logging.getLogger(__name__)


def create_mcp_server() -> Any:
    """Crea y configura el servidor MCP con herramientas de consulta y validación RAG."""
    if MCPServer is None:
        raise RuntimeError("La librería mcp no está instalada o no es compatible.")

    server = MCPServer(MCP_SERVER_NAME)

    @server.tool()
    def validar_documento_por_dni(
        dni: str,
        nombre_persona: Optional[str] = None,
        nombre_comercial: Optional[str] = None,
        actividad_economica: Optional[str] = None
    ) -> str:
        """
        Valida la información de un contribuyente a partir de su número de DNI y campos a cotejar.
        Retorna:
          - APROBADO: Si los campos coinciden exitosamente.
          - OBSERVADO: Si uno o varios campos no coinciden con los datos registrados.
          - NO_ENCONTRADO: Si el DNI no existe en el índice de AI Search.
        """
        query = ValidateFichaRucQuery(
            dni=dni,
            nombre_persona=nombre_persona,
            nombre_comercial=nombre_comercial,
            actividad_economica=actividad_economica
        )
        response = mediator.query(query)
        output = response.to_output_dict(include_datos=True)
        return json.dumps(output, ensure_ascii=False, indent=2)

    @server.tool()
    def consultar_ficha_ruc(dni: str) -> str:
        """
        Consulta y recupera los datos completos de una Ficha RUC registrada en Azure AI Search por DNI.
        Retorna nombre_persona, nombre_comercial, actividad_economica, ruc, etc.
        """
        query = GetFichaRucByDniQuery(dni=dni)
        doc = mediator.query(query)
        if not doc:
            return json.dumps({
                KEY_RESULTADO: RESULTADO_NO_ENCONTRADO,
                KEY_COMENTARIO: MSG_NO_ENCONTRADO
            }, ensure_ascii=False, indent=2)

        return json.dumps(doc.model_dump(by_alias=True), ensure_ascii=False, indent=2)

    @server.tool()
    def subir_documento_sunat(
        nombre_archivo: str,
        contenido_base64: str,
        content_type: str = CONTENT_TYPE_PDF
    ) -> str:
        """
        Sube un documento SUNAT (ej. Ficha RUC en PDF) al contenedor de Azure Blob Storage.
        """
        try:
            data = base64.b64decode(contenido_base64)
            cmd = UploadBlobCommand(
                blob_name=nombre_archivo,
                data=data,
                content_type=content_type
            )
            blob_url = mediator.send(cmd)
            return json.dumps({
                "status": "success",
                "message": f"Documento subido correctamente",
                "url": blob_url
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error subiendo documento: {str(e)}"
            }, ensure_ascii=False, indent=2)

    @server.tool()
    def indexar_ficha_ruc(
        dni: str,
        ruc: str,
        nombre_persona: str,
        nombre_comercial: str,
        actividad_economica: str,
        id: Optional[str] = None
    ) -> str:
        """
        Registra o actualiza directamente una Ficha RUC en el índice fichas-ruc-index de Azure AI Search.
        """
        try:
            doc_id = id or f"doc-{dni}"
            cmd = IndexFichaRucCommand(
                id=doc_id,
                dni=dni,
                ruc=ruc,
                nombre_persona=nombre_persona,
                nombre_comercial=nombre_comercial,
                actividad_economica=actividad_economica
            )
            success = mediator.send(cmd)
            return json.dumps({
                "status": "success" if success else "failed",
                "id": doc_id,
                "dni": dni
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error indexando ficha RUC: {str(e)}"
            }, ensure_ascii=False, indent=2)

    return server
