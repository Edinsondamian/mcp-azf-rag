"""
Capa Cross-Cutting: Constantes transversales del sistema.
Centraliza constantes de negocio, Azure, MCP, validaciones y formatos.
"""

# =============================================================================
# CONSTANTES DE RESULTADOS Y VALIDACIÓN (BUSINESS / CQRS)
# =============================================================================
RESULTADO_APROBADO = "APROBADO"
RESULTADO_OBSERVADO = "OBSERVADO"
RESULTADO_NO_ENCONTRADO = "NO_ENCONTRADO"

MSG_APROBADO = "Se valida correctamente el contenido"
MSG_NO_ENCONTRADO = "El valor recibido no fue encontrado en la base de conocimientos"
PLANTILLA_OBSERVACION = "- Campo {campo} no coincide con el valor"

# Nombres de campos para reporte de observaciones
CAMPO_NOMBRE_PERSONA = "NOMBRE PERSONA"
CAMPO_NOMBRE_COMERCIAL = "NOMBRE COMERCIAL"
CAMPO_ACTIVIDAD_ECONOMICA = "ACTIVIDAD ECONOMICA"
CAMPO_DNI = "DNI"
CAMPO_RUC = "RUC"

# Claves de salida JSON requeridas
KEY_RESULTADO = "RESULTADO"
KEY_COMENTARIO = "COMENTARIO"
KEY_DATOS = "DATOS"

# =============================================================================
# CONSTANTES DE AZURE AI SEARCH
# =============================================================================
DEFAULT_INDEX_NAME = "fichas-ruc-index"
DEFAULT_SEARCH_SERVICE_NAME = "search-ia-zat"

FIELD_ID = "id"
FIELD_DNI = "dni"
FIELD_RUC = "ruc"
FIELD_NOMBRE_PERSONA = "nombre_persona"
FIELD_NOMBRE_COMERCIAL = "nombre_comercial"
FIELD_ACTIVIDAD_ECONOMICA = "actividad_economica"

SEARCH_SELECTED_FIELDS = [
    FIELD_ID,
    FIELD_DNI,
    FIELD_RUC,
    FIELD_NOMBRE_PERSONA,
    FIELD_NOMBRE_COMERCIAL,
    FIELD_ACTIVIDAD_ECONOMICA
]

# =============================================================================
# CONSTANTES DE AZURE BLOB STORAGE
# =============================================================================
DEFAULT_CONTAINER_NAME = "namerag-poc"
CONTENT_TYPE_PDF = "application/pdf"
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_OCTET_STREAM = "application/octet-stream"

# =============================================================================
# CONSTANTES DE PROTOCOLO MCP Y AGENTES
# =============================================================================
MCP_SERVER_NAME = "mcp-azf-rag-tools"

TOOL_VALIDAR_DOCUMENTO = "validar_documento_por_dni"
TOOL_CONSULTAR_FICHA = "consultar_ficha_ruc"
TOOL_SUBIR_DOCUMENTO = "subir_documento_sunat"
TOOL_INDEXAR_FICHA = "indexar_ficha_ruc"

# =============================================================================
# CONSTANTES HTTP Y AZURE FUNCTIONS
# =============================================================================
HEADER_VALIDATION_RESULT = "X-Validation-Result"

# =============================================================================
# CONSTANTES DE AZURE OPENAI Y SKILLSET
# =============================================================================
DEFAULT_OPENAI_DEPLOYMENT = "gpt-5.6-luna"
DEFAULT_OPENAI_API_VERSION = "2024-02-15-preview"
DEFAULT_SKILLSET_NAME = "fichas-ruc-skillset"
DEFAULT_DATASOURCE_NAME = "namerag-poc-datasource"
DEFAULT_INDEXER_NAME = "fichas-ruc-indexer"
SKILL_EXTRACT_FICHA_ROUTE = "skills/extract-ficha"
