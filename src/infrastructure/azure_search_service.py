import logging
from typing import Optional, List, Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField
)

from ..config import settings
from ..domain.models import FichaRucDocument
from ..crosscutting.constants import (
    DEFAULT_INDEX_NAME,
    FIELD_ID,
    FIELD_DNI,
    FIELD_RUC,
    FIELD_NOMBRE_PERSONA,
    FIELD_NOMBRE_COMERCIAL,
    FIELD_ACTIVIDAD_ECONOMICA,
    SEARCH_SELECTED_FIELDS,
)

logger = logging.getLogger(__name__)


class AzureSearchService:
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        index_name: Optional[str] = None
    ):
        self.endpoint = endpoint or settings.AZURE_SEARCH_ENDPOINT
        self.api_key = api_key or settings.AZURE_SEARCH_API_KEY
        self.index_name = index_name or settings.AZURE_SEARCH_INDEX_NAME
        self.credential = AzureKeyCredential(self.api_key)
        self._search_client: Optional[SearchClient] = None
        self._index_client: Optional[SearchIndexClient] = None

    @property
    def search_client(self) -> SearchClient:
        if self._search_client is None:
            self._search_client = SearchClient(
                endpoint=self.endpoint,
                index_name=self.index_name,
                credential=self.credential
            )
        return self._search_client

    @property
    def index_client(self) -> SearchIndexClient:
        if self._index_client is None:
            self._index_client = SearchIndexClient(
                endpoint=self.endpoint,
                credential=self.credential
            )
        return self._index_client

    def ensure_index_exists(self) -> None:
        """Verifica o crea el índice fichas-ruc-index con el esquema indicado."""
        try:
            self.index_client.get_index(self.index_name)
            logger.info("El índice '%s' ya existe.", self.index_name)
        except Exception:
            logger.info("Creando el índice '%s'...", self.index_name)
            fields = [
                SimpleField(name=FIELD_ID, type=SearchFieldDataType.String, key=True),
                SearchableField(name=FIELD_DNI, type=SearchFieldDataType.String, filterable=True),
                SearchableField(name=FIELD_RUC, type=SearchFieldDataType.String, filterable=True),
                SearchableField(name=FIELD_NOMBRE_PERSONA, type=SearchFieldDataType.String),
                SearchableField(name=FIELD_NOMBRE_COMERCIAL, type=SearchFieldDataType.String),
                SearchableField(name=FIELD_ACTIVIDAD_ECONOMICA, type=SearchFieldDataType.String),
            ]
            index = SearchIndex(name=self.index_name, fields=fields)
            self.index_client.create_index(index)
            logger.info("Índice '%s' creado exitosamente.", self.index_name)

    def search_by_dni(self, dni: str) -> Optional[FichaRucDocument]:
        """
        Busca un registro en Azure AI Search filtrando por el número de DNI.
        """
        clean_dni = dni.strip()
        try:
            # Primero intentamos con filtro estricto OData
            results = list(
                self.search_client.search(
                    search_text="*",
                    filter=f"{FIELD_DNI} eq '{clean_dni}'",
                    select=SEARCH_SELECTED_FIELDS,
                    top=1
                )
            )

            # Si no encuentra por filtro, intentamos búsqueda por término
            if not results:
                results = list(
                    self.search_client.search(
                        search_text=clean_dni,
                        search_fields=[FIELD_DNI],
                        select=SEARCH_SELECTED_FIELDS,
                        top=1
                    )
                )

            if not results:
                logger.info("No se encontró ningún documento con DNI '%s'", clean_dni)
                return None

            item = results[0]
            return FichaRucDocument(
                id=str(item.get(FIELD_ID, clean_dni)),
                dni=str(item.get(FIELD_DNI, clean_dni)),
                ruc=str(item.get(FIELD_RUC, "")),
                nombre_persona=str(item.get(FIELD_NOMBRE_PERSONA, "")),
                nombre_comercial=str(item.get(FIELD_NOMBRE_COMERCIAL, "")),
                actividad_economica=str(item.get(FIELD_ACTIVIDAD_ECONOMICA, "")),
                search_score=item.get("@search.score", 1.0)
            )
        except Exception as e:
            logger.error("Error buscando en Azure AI Search por DNI %s: %s", clean_dni, e)
            raise e

    def index_document(self, doc: FichaRucDocument) -> bool:
        """Indexa o actualiza un documento en fichas-ruc-index."""
        try:
            payload: Dict[str, Any] = {
                FIELD_ID: doc.id,
                FIELD_DNI: doc.dni,
                FIELD_RUC: doc.ruc,
                FIELD_NOMBRE_PERSONA: doc.nombre_persona,
                FIELD_NOMBRE_COMERCIAL: doc.nombre_comercial,
                FIELD_ACTIVIDAD_ECONOMICA: doc.actividad_economica
            }
            result = self.search_client.upload_documents(documents=[payload])
            return bool(result and result[0].succeeded)
        except Exception as e:
            logger.error("Error indexando documento %s: %s", doc.id, e)
            raise e

    def list_all(self, top: int = 20) -> List[FichaRucDocument]:
        """Lista documentos indexados."""
        try:
            results = self.search_client.search(
                search_text="*",
                select=SEARCH_SELECTED_FIELDS,
                top=top
            )
            docs = []
            for item in results:
                docs.append(FichaRucDocument(
                    id=str(item.get(FIELD_ID, "")),
                    dni=str(item.get(FIELD_DNI, "")),
                    ruc=str(item.get(FIELD_RUC, "")),
                    nombre_persona=str(item.get(FIELD_NOMBRE_PERSONA, "")),
                    nombre_comercial=str(item.get(FIELD_NOMBRE_COMERCIAL, "")),
                    actividad_economica=str(item.get(FIELD_ACTIVIDAD_ECONOMICA, "")),
                    search_score=item.get("@search.score", 1.0)
                ))
            return docs
        except Exception as e:
            logger.error("Error listando documentos de Azure AI Search: %s", e)
            raise e
