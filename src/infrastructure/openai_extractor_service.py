"""
Servicio de infraestructura para extracción de información de Fichas RUC SUNAT
utilizando Azure OpenAI / Azure AI Foundry (modelo gpt-5.6-luna).
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from src.config import settings

logger = logging.getLogger(__name__)

SYSTEM_EXTRACTION_PROMPT = """Eres un extractor especializado en Fichas RUC de la SUNAT (Perú).
Extrae del texto del documento estrictamente los siguientes 5 campos en formato JSON:
- dni: Número de DNI del titular (8 dígitos numéricos). Si no figura explícito, extráelo de las posiciones 3 a 10 del RUC si comienza con 10.
- ruc: Número de RUC (11 dígitos numéricos).
- nombre_persona: Nombres y Apellidos del titular o Razón Social oficial en mayúsculas.
- nombre_comercial: Nombre comercial registrado. Si no tiene o figura un guión, retorna "-".
- actividad_economica: Código CIIU y descripción de la actividad económica principal. Si no tiene o figura un guión, retorna "-".

IMPORTANTE: Responde ÚNICAMENTE un objeto JSON válido con esas 5 claves, sin explicaciones adicionales."""


class OpenAIExtractorService:
    """Servicio que invoca Azure OpenAI para procesar texto de documentos y extraer campos estructurados."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: Optional[str] = None
    ):
        self.endpoint = (endpoint or settings.AZURE_OPENAI_ENDPOINT).rstrip("/")
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY
        self.deployment = deployment or settings.AZURE_OPENAI_DEPLOYMENT
        self.api_version = api_version or settings.AZURE_OPENAI_API_VERSION

    def extract_fields(self, text: str) -> Dict[str, str]:
        """
        Extrae los campos estructurados de una Ficha RUC a partir de su texto extraído.
        """
        if not text or not text.strip():
            logger.warning("Texto de entrada vacío para extracción LLM.")
            return {
                "dni": "",
                "ruc": "",
                "nombre_persona": "",
                "nombre_comercial": "-",
                "actividad_economica": "-"
            }

        url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"
        
        # Limitamos el texto a los primeros 12000 caracteres para optimizar tokens
        truncated_text = text[:12000]

        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT},
                {"role": "user", "content": f"Analiza y extrae los datos de esta Ficha RUC SUNAT:\n\n{truncated_text}"}
            ],
            "response_format": {"type": "json_object"},
            "max_completion_tokens": 600
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                resp_body = response.read().decode("utf-8")
                resp_json = json.loads(resp_body)
                content_str = resp_json["choices"][0]["message"]["content"]
                parsed = json.loads(content_str)
                
                result = {
                    "dni": str(parsed.get("dni", "")).strip(),
                    "ruc": str(parsed.get("ruc", "")).strip(),
                    "nombre_persona": str(parsed.get("nombre_persona", "")).strip().upper(),
                    "nombre_comercial": str(parsed.get("nombre_comercial", "-")).strip().upper() or "-",
                    "actividad_economica": str(parsed.get("actividad_economica", "-")).strip().upper() or "-"
                }
                logger.info("Extracción exitosa para DNI: %s | RUC: %s", result["dni"], result["ruc"])
                return result

        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            logger.error("Error HTTP al invocar Azure OpenAI (%s): %s", e.code, err_msg)
            raise RuntimeError(f"Azure OpenAI HTTP Error {e.code}: {err_msg}")
        except Exception as e:
            logger.error("Fallo inesperado al extraer con Azure OpenAI: %s", str(e))
            raise RuntimeError(f"Fallo en extracción LLM: {str(e)}")
