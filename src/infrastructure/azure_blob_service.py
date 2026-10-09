import logging
from typing import Optional, List
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings

from ..config import settings
from ..crosscutting.constants import CONTENT_TYPE_PDF

logger = logging.getLogger(__name__)


class AzureBlobService:
    def __init__(
        self,
        connection_string: Optional[str] = None,
        container_name: Optional[str] = None
    ):
        self.connection_string = connection_string or settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = container_name or settings.AZURE_STORAGE_CONTAINER_NAME
        self._blob_service_client: Optional[BlobServiceClient] = None
        self._container_client: Optional[ContainerClient] = None

    @property
    def blob_service_client(self) -> BlobServiceClient:
        if self._blob_service_client is None:
            self._blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        return self._blob_service_client

    @property
    def container_client(self) -> ContainerClient:
        if self._container_client is None:
            self._container_client = self.blob_service_client.get_container_client(self.container_name)
        return self._container_client

    def ensure_container_exists(self) -> None:
        """Verifica o crea el contenedor de almacenamiento si no existe."""
        try:
            if not self.container_client.exists():
                self.container_client.create_container()
                logger.info("Contenedor '%s' creado exitosamente.", self.container_name)
        except Exception as e:
            logger.error("Error asegurando existencia del contenedor: %s", e)
            raise e

    def upload_file(
        self,
        blob_name: str,
        data: bytes,
        content_type: str = CONTENT_TYPE_PDF,
        overwrite: bool = True
    ) -> str:
        """
        Sube un archivo (Doc SUNAT, Ficha RUC, etc.) a Azure Blob Storage.
        Retorna la URL del blob o su nombre.
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            content_settings = ContentSettings(content_type=content_type)
            blob_client.upload_blob(
                data,
                overwrite=overwrite,
                content_settings=content_settings
            )
            logger.info("Blob '%s' subido exitosamente al contenedor '%s'.", blob_name, self.container_name)
            return blob_client.url
        except Exception as e:
            logger.error("Error subiendo blob '%s': %s", blob_name, e)
            raise e

    def download_file(self, blob_name: str) -> bytes:
        """Descarga el contenido de un blob."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            return download_stream.readall()
        except Exception as e:
            logger.error("Error descargando blob '%s': %s", blob_name, e)
            raise e

    def list_files(self) -> List[str]:
        """Lista los nombres de los blobs en el contenedor."""
        try:
            return [b.name for b in self.container_client.list_blobs()]
        except Exception as e:
            logger.error("Error listando blobs: %s", e)
            raise e
