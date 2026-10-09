from dataclasses import dataclass
from typing import Optional
from ..bus import Command, CommandHandler
from ...infrastructure.azure_blob_service import AzureBlobService


@dataclass
class UploadBlobCommand(Command):
    blob_name: str
    data: bytes
    content_type: str = "application/pdf"
    overwrite: bool = True


class UploadBlobCommandHandler(CommandHandler[UploadBlobCommand, str]):
    def __init__(self, blob_service: Optional[AzureBlobService] = None) -> None:
        self.blob_service = blob_service or AzureBlobService()

    def handle(self, command: UploadBlobCommand) -> str:
        return self.blob_service.upload_file(
            blob_name=command.blob_name,
            data=command.data,
            content_type=command.content_type,
            overwrite=command.overwrite
        )
