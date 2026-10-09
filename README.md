# MCP Azure Function RAG - CQRS Document Validation

Sistema de validación documental SUNAT y recuperación aumentada por generación (RAG) implementado como un **Servidor MCP (Model Context Protocol)** y **Azure Functions v2**, desacoplado mediante el patrón de arquitectura **CQRS (Command Query Responsibility Segregation)**, conectado a **Azure AI Search** y **Azure Blob Storage**.

Desarrollado para **Python 3.14** (compatible con Python >= 3.12).

---

## 📐 Arquitectura del Sistema

El proyecto implementa la arquitectura descrita en el flujo del Agente Documental:

```mermaid
flowchart TD
    subgraph Agente["4 · Agente Documental"]
        A[Agente de IA / LLM]
    end

    subgraph MCP_AZF["Azure Function / Servidor MCP (Tools)"]
        direction TB
        B[Bus CQRS - Mediator]
        Q[Queries: Búsqueda y Validación]
        C[Commands: Ingesta e Indexación]
        B --> Q
        B --> C
    end

    subgraph Azure_Cloud["Infraestructura Azure"]
        S[(Azure Blob Storage\nContenedor: namerag-poc)]
        AIS[(Azure AI Search\nÍndice: fichas-ruc-index)]
        DOC[Documento SUNAT PDF] -->|Carga / Ingesta| S
        S -->|Indexer BlobCreated| AIS
    end

    A -->|Consulta / Tool Call: DNI + Campos| MCP_AZF
    Q -->|Consulta / Filtro OData| AIS
    C -->|Subida de Archivos| S
    C -->|Indexación Directa| AIS
    MCP_AZF -->|Respuesta: Aprobado / Observado / No Encontrado| A
```

---

## ⚡ Patrón CQRS (Command Query Responsibility Segregation)

El sistema separa estrictamente las operaciones de lectura de las operaciones de modificación de estado:

### 🔍 Queries (Lecturas y Validaciones)
- **`GetFichaRucByDniQuery`**: Consulta directa en Azure AI Search por DNI (`filter="dni eq '{dni}'"`).
- **`ValidateFichaRucQuery`**: Valida y coteja los datos proporcionados (`DNI`, `NOMBRE_PERSONA`, `NOMBRE_COMERCIAL`, `ACTIVIDAD_ECONOMICA`) contra la base de conocimientos.
  - **APROBADO**: Si todos los campos coinciden.
  - **OBSERVADO**: Si uno o varios campos difieren.
  - **NO_ENCONTRADO**: Si el DNI no existe en el índice.

### ✍️ Commands (Mutaciones e Ingesta)
- **`IndexFichaRucCommand`**: Registra o actualiza directamente un registro en el índice `fichas-ruc-index`.
- **`UploadBlobCommand`**: Carga documentos físicos (PDF/DOC) en el contenedor de Azure Blob Storage (`namerag-poc`).

### 🚌 CQRS Mediator
El bus `CQRSMediator` desacopla los controladores HTTP y las herramientas MCP de la lógica de dominio.

---

## 📄 Esquema del Índice en Azure AI Search

El índice utilizado es **`fichas-ruc-index`**:

| Campo | Tipo | Key | Searchable | Filterable | Retrievable |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `id` | `Edm.String` | ✅ Sí | ❌ No | ❌ No | ✅ Sí |
| `dni` | `Edm.String` | ❌ No | ✅ Sí | ✅ Sí | ✅ Sí |
| `ruc` | `Edm.String` | ❌ No | ✅ Sí | ✅ Sí | ✅ Sí |
| `nombre_persona` | `Edm.String` | ❌ No | ✅ Sí | ❌ No | ✅ Sí |
| `nombre_comercial` | `Edm.String` | ❌ No | ✅ Sí | ❌ No | ✅ Sí |
| `actividad_economica` | `Edm.String` | ❌ No | ✅ Sí | ❌ No | ✅ Sí |

---

## 📥 Entradas y Salidas de la Validación

### Entradas (Request)
- `dni`: Número de DNI (Ej: `"12345678"`) - **Obligatorio**
- `nombre_persona`: Nombre completo (Ej: `"PEREZ GARCIA JUAN"`) - *Opcional*
- `nombre_comercial`: Nombre comercial (Ej: `"JPG IMPORT & EXPORT"`) - *Opcional*
- `actividad_economica`: Actividad económica (Ej: `"4690 - VENTA AL POR MAYOR NO ESPECIALIZADA"`) - *Opcional*

### Salidas (Response)

#### 1. Caso APROBADO (HTTP 200)
```json
{
  "RESULTADO": "APROBADO",
  "COMENTARIO": "Se valida correctamente el contenido"
}
```

#### 2. Caso OBSERVADO (HTTP 200)
```json
{
  "RESULTADO": "OBSERVADO",
  "COMENTARIO": "- Campo NOMBRE COMERCIAL no coincide con el valor\n- Campo ACTIVIDAD ECONOMICA no coincide con el valor"
}
```

#### 3. Caso NO ENCONTRADO (HTTP 200 / 204)
```json
{
  "RESULTADO": "NO_ENCONTRADO",
  "COMENTARIO": "El valor recibido no fue encontrado en la base de conocimientos"
}
```

---

## 🚀 Instalación y Puesta en Marcha

### 1. Clonar y cambiar a la rama
```bash
git checkout feature/V1
```

### 2. Crear y activar el entorno virtual
```powershell
# En Windows PowerShell
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Variables de Entorno (`.env`)
Configurar el archivo `.env` a partir de la plantilla `.env.example`:
```bash
cp .env.example .env
```

Configurar las siguientes variables en `.env`:
```ini
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=<tu-storage-account>;AccountKey=<tu-account-key>;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=namerag-poc

AZURE_SEARCH_SERVICE_NAME=search-ia-zat
AZURE_SEARCH_ENDPOINT=https://<tu-servicio-search>.search.windows.net
AZURE_SEARCH_API_KEY=<tu-search-api-key>
AZURE_SEARCH_INDEX_NAME=fichas-ruc-index

PYTHON_VERSION=3.14
```

---

---

## 🧪 Pruebas y Verificación

El sistema cuenta con una batería integral de pruebas que cubren pruebas unitarias automatizadas y pruebas de integración en vivo contra los servicios de Azure AI Search y Blob Storage.

### 📊 Matriz de Casos de Uso Probados

| ID | Caso de Uso | DNI | Entrada Evaluada | Resultado | Estado |
| :---: | :--- | :---: | :--- | :---: | :---: |
| **CU-01** | Coincidencia Exacta | `12345678` | DNI, Nombre, Comercial y Actividad idénticos | `APROBADO` | ✅ PASS |
| **CU-02** | Resiliencia de Formato | `70123456` | Minúsculas, tildes y espacios redundantes | `APROBADO` | ✅ PASS |
| **CU-03** | Nombre Comercial Discrepante | `45678901` | Nombre comercial erróneo | `OBSERVADO` | ✅ PASS |
| **CU-04** | Múltiples Discrepancias | `09876543` | Nombre de persona y actividad económica erróneos | `OBSERVADO` | ✅ PASS |
| **CU-05** | DNI No Registrado | `99999999` | DNI inexistente en la base de conocimientos | `NO_ENCONTRADO` | ✅ PASS |
| **CU-06** | Solo DNI | `41239876` | Únicamente número de DNI existente | `APROBADO` | ✅ PASS |
| **CU-07** | Consulta Directa Ficha RUC | `72345678` | Consulta por DNI para recuperar datos completos | `DOC RECUPERADO` | ✅ PASS |
| **CU-08** | Orquestación Agente | `48765432` | Invocación mediante `DocumentAgent.procesar_solicitud` | `APROBADO` | ✅ PASS |
| **CU-09** | Herramienta MCP | `87654321` | Tool Call MCP `validar_documento_por_dni` | `APROBADO` | ✅ PASS |

---

### 📝 Detalle de Ejemplos y Respuestas

#### Caso 1: Aprobado por Coincidencia Exacta (CU-01)
- **Input:**
  ```json
  {
    "dni": "12345678",
    "nombre_persona": "PEREZ GARCIA JUAN",
    "nombre_comercial": "JPG IMPORT & EXPORT",
    "actividad_economica": "4690 - VENTA AL POR MAYOR NO ESPECIALIZADA"
  }
  ```
- **Output:**
  ```json
  {
    "RESULTADO": "APROBADO",
    "COMENTARIO": "Se valida correctamente el contenido"
  }
  ```

#### Caso 2: Observado por Múltiples Discrepancias (CU-04)
- **Input:**
  ```json
  {
    "dni": "09876543",
    "nombre_persona": "HUAMAN ROJAS CARLOS ENRIQUE",
    "nombre_comercial": "TRANSPORTE & LOGISTICA RAPIDO",
    "actividad_economica": "8610 - ACTIVIDADES DE HOSPITALES"
  }
  ```
- **Output:**
  ```json
  {
    "RESULTADO": "OBSERVADO",
    "COMENTARIO": "- Campo NOMBRE PERSONA no coincide con el valor\n- Campo ACTIVIDAD ECONOMICA no coincide con el valor"
  }
  ```

#### Caso 3: No Encontrado (CU-05)
- **Input:**
  ```json
  {
    "dni": "99999999"
  }
  ```
- **Output:**
  ```json
  {
    "RESULTADO": "NO_ENCONTRADO",
    "COMENTARIO": "El valor recibido no fue encontrado en la base de conocimientos"
  }
  ```

---

### 💻 Comandos de Ejecución de Pruebas

#### 1. Ejecutar la Batería Completa de Casos de Uso
Ejecuta los 9 casos de uso documentados arriba en vivo contra Azure:
```bash
python scripts/run_all_use_cases.py
```

#### 2. Ejecutar Tests Unitarios (Pytest)
Ejecuta las pruebas unitarias aisladas de la lógica CQRS, mediador y normalización:
```bash
pytest -v
```

#### 3. Sembrar o Actualizar Datos de Prueba en Azure
Indexa los 8 contribuyentes de prueba en `fichas-ruc-index` y sube los blobs a Azure:
```bash
python scripts/seed_sample_data.py
```

---

## 🔌 Ejecución de Servidores

### Opción A: Servidor MCP (Model Context Protocol)
El servidor MCP expone las herramientas para agentes de Inteligencia Artificial (Claude Desktop, Cursor, Antigravity, AutoGen, etc.).

**Modo Stdio (Estándar para Agentes de Escritorio):**
```bash
python mcp_server.py --transport stdio
```

**Modo SSE (Servidor HTTP Streaming):**
```bash
python mcp_server.py --transport sse --port 8000
```

#### Herramientas MCP Disponibles:
1. `validar_documento_por_dni(dni, nombre_persona, nombre_comercial, actividad_economica)`
2. `consultar_ficha_ruc(dni)`
3. `subir_documento_sunat(nombre_archivo, contenido_base64)`
4. `indexar_ficha_ruc(dni, ruc, nombre_persona, nombre_comercial, actividad_economica)`

---

### Opción B: Azure Function (Local con Azure Functions Core Tools)
```bash
func start
```

#### Endpoints expuestos:
- `POST /api/validate` o `GET /api/validate?dni=12345678` -> Validación CQRS.
- `GET /api/document/{dni}` -> Recuperación de ficha RUC.
- `POST /api/document` -> Indexación de documento en Azure Search.
- `POST /api/upload` -> Carga de archivo a Azure Blob Storage.
- `POST /api/mcp/tools/call` -> Invocación HTTP de herramientas MCP.
- `GET /api/health` -> Chequeo de salud y conectividad con Azure.

---

## 🤖 Módulo de Agentes (`agents/`)
En la carpeta [`agents/`](file:///f:/TRABAJOS/HARKAY/mcp-azf-rag/agents) se encuentra la implementación del **Agente Documental**:
- [`document_agent.py`](file:///f:/TRABAJOS/HARKAY/mcp-azf-rag/agents/document_agent.py): Orquestador de solicitudes y validaciones.
- [`prompts.py`](file:///f:/TRABAJOS/HARKAY/mcp-azf-rag/agents/prompts.py): System prompts y reglas de negocio del Agente Documental.
- [`README.md`](file:///f:/TRABAJOS/HARKAY/mcp-azf-rag/agents/README.md): Documentación específica del agente.
