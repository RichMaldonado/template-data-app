from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MetaGerenciaBase(BaseModel):
    ciclo: int = Field(..., description="Ciclo comercial en formato YYYYCC (ej. 202601)")
    gerencia: str = Field(..., description="Codigo o nombre de la gerencia (ej. GV_NORTE)")
    meta_monto: float = Field(..., ge=0.0, description="Meta financiera de facturacion neta")
    meta_consultoras: int = Field(..., ge=0, description="Meta de consultoras activas")
    observaciones: Optional[str] = Field(None, description="Comentarios o justificacion")
    usuario_registro: Optional[str] = Field("analista", description="Usuario que registra la meta")

class MetaGerenciaCreate(MetaGerenciaBase):
    pass

class MetaGerenciaUpdate(BaseModel):
    meta_monto: Optional[float] = Field(None, ge=0.0)
    meta_consultoras: Optional[int] = Field(None, ge=0)
    observaciones: Optional[str] = None
    usuario_registro: Optional[str] = "analista"

class MetaGerenciaResponse(MetaGerenciaBase):
    id: int
    creado_en: Optional[str]
    actualizado_en: Optional[str]

    class Config:
        from_attributes = True
