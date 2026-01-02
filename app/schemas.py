from datetime import date
from typing import Optional, List
from pydantic import BaseModel

# ============ CLASES Y ATRIBUTOS ============

class ClaseEquipoBase(BaseModel):
    nombre: str
    familia: Optional[str] = None
    descripcion: Optional[str] = None

class ClaseEquipoCreate(ClaseEquipoBase):
    pass

class ClaseEquipoOut(ClaseEquipoBase):
    id: int
    
    class Config:
        from_attributes = True


class AtributoClaseBase(BaseModel):
    nombre_atributo: str
    tipo_dato: str = "texto"
    unidad: Optional[str] = None
    obligatorio: bool = False

class AtributoClaseCreate(AtributoClaseBase):
    clase_id: int

class AtributoClaseOut(AtributoClaseBase):
    id: int
    clase_id: int
    
    class Config:
        from_attributes = True


class ValorAtributoBase(BaseModel):
    atributo_id: int
    valor_texto: Optional[str] = None
    valor_numero: Optional[float] = None

class ValorAtributoOut(ValorAtributoBase):
    id: int
    
    class Config:
        from_attributes = True


# ============ EQUIPOS ============

class EquipoBase(BaseModel):
    area: str
    linea: str
    equipo: str
    sistema: str
    componente: str
    codigo_interno: str
    descripcion: Optional[str] = None
    ubicacion: Optional[str] = None
    criticidad: Optional[str] = None
    estado: Optional[str] = None
    fecha_alta: Optional[date] = None
    clase_equipo_id: Optional[int] = None
    activo: bool = True

class EquipoCreate(EquipoBase):
    atributos: List[ValorAtributoBase] = []

class EquipoUpdate(BaseModel):
    area: Optional[str] = None
    linea: Optional[str] = None
    equipo: Optional[str] = None
    sistema: Optional[str] = None
    componente: Optional[str] = None
    descripcion: Optional[str] = None
    ubicacion: Optional[str] = None
    criticidad: Optional[str] = None
    estado: Optional[str] = None
    activo: Optional[bool] = None

class EquipoOut(EquipoBase):
    id: int
    atributos: List[ValorAtributoOut] = []
    
    class Config:
        from_attributes = True


# ============ AVISOS Y OT ============

class AvisoBase(BaseModel):
    equipo_id: int
    descripcion_aviso: str
    criticidad_aviso: Optional[str] = None
    prioridad: Optional[str] = None
    fecha_solicitud: date
    estado_aviso: str = "Pendiente"

class AvisoCreate(AvisoBase):
    pass

class AvisoOut(AvisoBase):
    id: int
    
    class Config:
        from_attributes = True
