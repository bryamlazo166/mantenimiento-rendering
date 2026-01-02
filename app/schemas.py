from datetime import date
from typing import Optional
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
    atributos: list[ValorAtributoBase] = []

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
    fecha_alta: Optional[date] = None
    clase_equipo_id: Optional[int] = None
    activo: Optional[bool] = None
    atributos: Optional[list[ValorAtributoBase]] = None

class EquipoOut(EquipoBase):
    id: int
    atributos: list[ValorAtributoOut] = []
    
    class Config:
        from_attributes = True


# ============ AVISOS ============

class AvisoBase(BaseModel):
    equipo_id: int
    descripcion_aviso: str
    criticidad_aviso: Optional[str] = None
    prioridad: Optional[str] = None
    fecha_solicitud: date
    fecha_tratamiento: Optional[date] = None
    fecha_programacion: Optional[date] = None
    estado_aviso: str = "Pendiente"
    solicitante: Optional[str] = None

class AvisoCreate(AvisoBase):
    pass

class AvisoUpdate(BaseModel):
    descripcion_aviso: Optional[str] = None
    criticidad_aviso: Optional[str] = None
    prioridad: Optional[str] = None
    fecha_tratamiento: Optional[date] = None
    fecha_programacion: Optional[date] = None
    estado_aviso: Optional[str] = None

class AvisoOut(AvisoBase):
    id: int
    
    class Config:
        from_attributes = True


# ============ ÓRDENES DE TRABAJO ============

class OrdenTrabajoBase(BaseModel):
    aviso_id: int
    numero_ot: str
    tipo_mantenimiento: Optional[str] = None
    actividad: Optional[str] = None
    tecnico: Optional[str] = None
    turno: Optional[str] = None
    especialidad: Optional[str] = None
    proveedor: Optional[str] = None
    fecha_inicio_programada: Optional[date] = None
    fecha_termino_programada: Optional[date] = None
    fecha_termino_real: Optional[date] = None
    plan_hh_parcial: Optional[float] = None
    plan_hh_total: Optional[float] = None
    cant_tecnicos_plan: Optional[int] = None
    real_hh_parcial: Optional[float] = None
    real_hh_total: Optional[float] = None
    cant_tecnicos_real: Optional[int] = None
    check_materiales: Optional[str] = None
    numero_rq: Optional[str] = None
    fecha_real_rq: Optional[date] = None
    fecha_estimada_rq: Optional[date] = None
    porcentaje_avance: float = 0.0
    estado_ot: str = "Abierta"
    observaciones: Optional[str] = None
    antiguedad: Optional[int] = None

class OrdenTrabajoCreate(OrdenTrabajoBase):
    pass

class OrdenTrabajoUpdate(BaseModel):
    tipo_mantenimiento: Optional[str] = None
    actividad: Optional[str] = None
    tecnico: Optional[str] = None
    turno: Optional[str] = None
    fecha_termino_real: Optional[date] = None
    real_hh_parcial: Optional[float] = None
    real_hh_total: Optional[float] = None
    cant_tecnicos_real: Optional[int] = None
    check_materiales: Optional[str] = None
    numero_rq: Optional[str] = None
    fecha_real_rq: Optional[date] = None
    porcentaje_avance: Optional[float] = None
    estado_ot: Optional[str] = None
    observaciones: Optional[str] = None

class OrdenTrabajoOut(OrdenTrabajoBase):
    id: int
    
    class Config:
        from_attributes = True
