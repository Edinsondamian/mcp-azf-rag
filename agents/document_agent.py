"""
Implementación del Agente Documental SUNAT.
Conecta los requerimientos del usuario con las herramientas MCP / Bus CQRS.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Permitir ejecución directa y como paquete
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.application.bus import mediator
from src.application.queries import (
    ValidateFichaRucQuery,
    GetFichaRucByDniQuery
)
from src.application.commands import (
    IndexFichaRucCommand,
    UploadBlobCommand
)
try:
    from .prompts import AGENT_DOCUMENTAL_SYSTEM_PROMPT
except (ImportError, ValueError):
    from agents.prompts import AGENT_DOCUMENTAL_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class DocumentAgent:
    """
    Agente documental que orquesta las consultas y validaciones RAG.
    Interactúa con Azure AI Search y Azure Blob Storage a través del bus CQRS.
    """

    def __init__(self, name: str = "AgenteDocumentalSUNAT"):
        self.name = name
        self.system_prompt = AGENT_DOCUMENTAL_SYSTEM_PROMPT

    def procesar_solicitud(
        self,
        dni: str,
        nombre_persona: Optional[str] = None,
        nombre_comercial: Optional[str] = None,
        actividad_economica: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa una solicitud de validación de documento según el diagrama de arquitectura:
        request: DNI, NOMBRE PERSONA, NOMBRE COMERCIAL Y ACTIVIDAD ECONOMICA
        response:
          - APROBADO: Si todo el resultado de los campos coinciden.
          - OBSERVADO: Si uno o más campos no coinciden.
          - NO_ENCONTRADO: Si el DNI no existe en el índice de AI Search.
        """
        logger.info("Agente [%s] validando DNI %s", self.name, dni)

        query = ValidateFichaRucQuery(
            dni=dni,
            nombre_persona=nombre_persona,
            nombre_comercial=nombre_comercial,
            actividad_economica=actividad_economica
        )

        response = mediator.query(query)
        output = response.to_output_dict(include_datos=False)
        return output

    def consultar_contribuyente(self, dni: str) -> Dict[str, Any]:
        """Consulta los datos del contribuyente por DNI."""
        query = GetFichaRucByDniQuery(dni=dni)
        doc = mediator.query(query)
        if not doc:
            return {
                "RESULTADO": "NO_ENCONTRADO",
                "COMENTARIO": "El valor recibido no fue encontrado en la base de conocimientos"
            }
        return doc.model_dump(by_alias=True)

    def ingestar_documento(
        self,
        id: str,
        dni: str,
        ruc: str,
        nombre_persona: str,
        nombre_comercial: str,
        actividad_economica: str
    ) -> bool:
        """Ingesta e indexa un documento en Azure AI Search."""
        cmd = IndexFichaRucCommand(
            id=id,
            dni=dni,
            ruc=ruc,
            nombre_persona=nombre_persona,
            nombre_comercial=nombre_comercial,
            actividad_economica=actividad_economica
        )
        return mediator.send(cmd)


if __name__ == "__main__":
    agent = DocumentAgent()
    print("=== Test Agente Documental ===")
    test_res = agent.procesar_solicitud(
        dni="12345678",
        nombre_persona="PEREZ GARCIA JUAN",
        nombre_comercial="JPG IMPORT & EXPORT",
        actividad_economica="4690 - VENTA AL POR MAYOR NO ESPECIALIZADA"
    )
    print(json.dumps(test_res, ensure_ascii=False, indent=2))
