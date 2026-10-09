from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ResultadoValidacion(str, Enum):
    APROBADO = "APROBADO"
    OBSERVADO = "OBSERVADO"
    NO_ENCONTRADO = "NO_ENCONTRADO"


class FichaRucDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    dni: str
    ruc: str
    nombre_persona: str
    nombre_comercial: str
    actividad_economica: str
    search_score: Optional[float] = Field(default=None, alias="@search.score")


class ValidationInput(BaseModel):
    dni: str = Field(..., description="Número de DNI a consultar/validar")
    nombre_persona: Optional[str] = Field(default=None, description="Nombre completo de la persona para comparación")
    nombre_comercial: Optional[str] = Field(default=None, description="Nombre comercial para comparación")
    actividad_economica: Optional[str] = Field(default=None, description="Actividad económica para comparación")


class ValidationResponse(BaseModel):
    RESULTADO: ResultadoValidacion
    COMENTARIO: str
    DATOS: Optional[dict[str, Any]] = Field(default=None, description="Detalles del documento encontrado si aplica")

    def to_output_dict(self, include_datos: bool = False) -> dict[str, Any]:
        """Devuelve el formato limpio requerido."""
        result: dict[str, Any] = {
            "RESULTADO": self.RESULTADO.value,
            "COMENTARIO": self.COMENTARIO
        }
        if include_datos and self.DATOS:
            result["DATOS"] = self.DATOS
        return result
