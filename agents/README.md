# Agente Documental SUNAT (Herramientas, Conocimiento e Ingesta)

Este módulo implementa el Agente Documental que opera sobre la infraestructura Azure AI Search y Azure Blob Storage mediante el protocolo **MCP (Model Context Protocol)** y el patrón **CQRS**.

---

## 🏗️ Flujo de Arquitectura

```
                        ┌───────────────────────────────┐
                        │      Agente Documental        │
                        │    (LLM / Chat / Ingesta)     │
                        └──────────────┬────────────────┘
                                       │
                      Invocación MCP / HTTP Request
                                       │
                                       ▼
                        ┌───────────────────────────────┐
                        │   MCP Azure Function (Tools)  │
                        │    (Patrón CQRS / Mediator)   │
                        └───────┬───────────────┬───────┘
                                │               │
                     Lectura (Queries)   Escritura (Commands)
                                │               │
                                ▼               ▼
                 ┌────────────────────┐   ┌────────────────────────┐
                 │  Azure AI Search   │   │  Azure Blob Storage    │
                 │ (fichas-ruc-index) │   │     (namerag-poc)      │
                 └────────────────────┘   └────────────────────────┘
```

---

## 🛠️ Herramientas MCP Expuestas para el Agente

### 1. `validar_documento_por_dni`
Coteja la información proporcionada contra la base de conocimientos de Azure AI Search.
- **Parámetros:**
  - `dni` (string, obligatorio): Número de DNI del contribuyente.
  - `nombre_persona` (string, opcional): Nombre completo a comparar.
  - `nombre_comercial` (string, opcional): Nombre comercial a comparar.
  - `actividad_economica` (string, opcional): Actividad económica a comparar.
- **Retorno:**
  JSON con `RESULTADO` (`APROBADO`, `OBSERVADO`, `NO_ENCONTRADO`) y `COMENTARIO`.

### 2. `consultar_ficha_ruc`
Recupera los datos completos indexados de un contribuyente por su DNI.
- **Parámetros:**
  - `dni` (string, obligatorio): DNI a buscar.

### 3. `subir_documento_sunat`
Sube archivos físicos (PDFs de Ficha RUC, etc.) al contenedor Blob Storage.

### 4. `indexar_ficha_ruc`
Registra o actualiza directamente un documento en `fichas-ruc-index`.

---

## 📋 Ejemplos de Respuestas del Agente

### Caso 1: Aprobado
```json
{
  "RESULTADO": "APROBADO",
  "COMENTARIO": "Se valida correctamente el contenido"
}
```

### Caso 2: Observado (Diferencias encontradas)
```json
{
  "RESULTADO": "OBSERVADO",
  "COMENTARIO": "- Campo NOMBRE PERSONA no coincide con el valor\n- Campo ACTIVIDAD ECONOMICA no coincide con el valor"
}
```

### Caso 3: No Encontrado
```json
{
  "RESULTADO": "NO_ENCONTRADO",
  "COMENTARIO": "El valor recibido no fue encontrado en la base de conocimientos"
}
```
