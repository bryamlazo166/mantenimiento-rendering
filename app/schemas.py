
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
    porcentaje_avance: Optional[float] = None
    estado_ot: Optional[str] = None
    observaciones: Optional[str] = None
    antiguedad: Optional[int] = None

class OrdenTrabajoOut(OrdenTrabajoBase):
    id: int
    
    class Config:
        from_attributes = True
