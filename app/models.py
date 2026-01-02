from sqlalchemy import Column, Integer, String, Date, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

# ============ MAESTRO DE ACTIVOS ============

class ClaseEquipo(Base):
    """Catálogo de tipos: Motor eléctrico, Bomba, Reductor, Polea, etc."""
    __tablename__ = "clases_equipo"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)  # Motor eléctrico
    familia = Column(String(50))  # Rotativo, Estático, Eléctrico, Instrumentación
    descripcion = Column(Text, nullable=True)
    
    # Relaciones
    atributos = relationship("AtributoClase", back_populates="clase")
    equipos = relationship("Equipo", back_populates="clase_equipo")


class AtributoClase(Base):
    """Define qué atributos técnicos debe tener cada clase"""
    __tablename__ = "atributos_clase"
    
    id = Column(Integer, primary_key=True, index=True)
    clase_id = Column(Integer, ForeignKey("clases_equipo.id"), nullable=False)
    nombre_atributo = Column(String(100), nullable=False)  # HP, Tensión, Diámetro
    tipo_dato = Column(String(20), default="texto")  # texto, numero, lista
    unidad = Column(String(20), nullable=True)  # V, HP, mm, RPM
    obligatorio = Column(Boolean, default=False)
    
    # Relaciones
    clase = relationship("ClaseEquipo", back_populates="atributos")
    valores = relationship("ValorAtributoEquipo", back_populates="atributo")


class Equipo(Base):
    """Maestro de equipos: jerarquía + info general"""
    __tablename__ = "equipos"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Jerarquía (5 niveles)
    area = Column(String(100), index=True, nullable=False)
    linea = Column(String(100), index=True, nullable=False)
    equipo = Column(String(100), index=True, nullable=False)
    sistema = Column(String(100), index=True, nullable=False)  # tu "Sistema" = Sub-equipo
    componente = Column(String(100), index=True, nullable=False)
    
    # Datos generales
    codigo_interno = Column(String(50), unique=True, index=True, nullable=False)
    descripcion = Column(Text)
    ubicacion = Column(String(200))
    criticidad = Column(String(20))  # Alta, Media, Baja
    estado = Column(String(50))  # Operativo, Parado, En mantenimiento
    fecha_alta = Column(Date, nullable=True)
    
    # Vínculo a clase de equipo (para atributos técnicos)
    clase_equipo_id = Column(Integer, ForeignKey("clases_equipo.id"), nullable=True)
    
    activo = Column(Boolean, default=True)
    
    # Relaciones
    clase_equipo = relationship("ClaseEquipo", back_populates="equipos")
    atributos_valores = relationship("ValorAtributoEquipo", back_populates="equipo", cascade="all, delete-orphan")
    avisos = relationship("Aviso", back_populates="equipo")


class ValorAtributoEquipo(Base):
    """Valores concretos de atributos técnicos por equipo"""
    __tablename__ = "valores_atributo_equipo"
    
    id = Column(Integer, primary_key=True, index=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    atributo_id = Column(Integer, ForeignKey("atributos_clase.id"), nullable=False)
    
    valor_texto = Column(String(200), nullable=True)
    valor_numero = Column(Float, nullable=True)
    
    # Relaciones
    equipo = relationship("Equipo", back_populates="atributos_valores")
    atributo = relationship("AtributoClase", back_populates="valores")


# ============ GESTIÓN DE MANTENIMIENTO ============

class Aviso(Base):
    """Solicitudes de mantenimiento (work requests)"""
    __tablename__ = "avisos"
    
    id = Column(Integer, primary_key=True, index=True)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    
    descripcion_aviso = Column(Text, nullable=False)
    criticidad_aviso = Column(String(20))  # Alta, Media, Baja
    prioridad = Column(String(20))
    
    fecha_solicitud = Column(Date, nullable=False)
    fecha_tratamiento = Column(Date, nullable=True)
    fecha_programacion = Column(Date, nullable=True)
    
    estado_aviso = Column(String(50), default="Pendiente")  # Pendiente, En proceso, Cerrado
    solicitante = Column(String(100), nullable=True)
    
    # Relaciones
    equipo = relationship("Equipo", back_populates="avisos")
    ordenes = relationship("OrdenTrabajo", back_populates="aviso")


class OrdenTrabajo(Base):
    """Órdenes de trabajo (work orders)"""
    __tablename__ = "ordenes_trabajo"
    
    id = Column(Integer, primary_key=True, index=True)
    aviso_id = Column(Integer, ForeignKey("avisos.id"), nullable=False)
    
    numero_ot = Column(String(50), unique=True, index=True, nullable=False)
    tipo_mantenimiento = Column(String(50))  # Correctivo, Preventivo, Predictivo
    actividad = Column(Text)
    
    # Asignación
    tecnico = Column(String(100))
    turno = Column(String(20))
    especialidad = Column(String(50))
    proveedor = Column(String(100), nullable=True)
    
    # Fechas
    fecha_inicio_programada = Column(Date, nullable=True)
    fecha_termino_programada = Column(Date, nullable=True)
    fecha_termino_real = Column(Date, nullable=True)
    
    # Planificación HH
    plan_hh_parcial = Column(Float, nullable=True)
    plan_hh_total = Column(Float, nullable=True)
    cant_tecnicos_plan = Column(Integer, nullable=True)
    
    # Real HH
    real_hh_parcial = Column(Float, nullable=True)
    real_hh_total = Column(Float, nullable=True)
    cant_tecnicos_real = Column(Integer, nullable=True)
    
    # Materiales
    check_materiales = Column(String(20), nullable=True)  # OK, Pendiente
    numero_rq = Column(String(50), nullable=True)
    fecha_real_rq = Column(Date, nullable=True)
    fecha_estimada_rq = Column(Date, nullable=True)
    
    # Control
    porcentaje_avance = Column(Float, default=0.0)
    estado_ot = Column(String(50), default="Abierta")  # Abierta, En ejecución, Cerrada
    observaciones = Column(Text, nullable=True)
    antiguedad = Column(Integer, nullable=True)  # días desde solicitud o inicio
    
    # Relaciones
    aviso = relationship("Aviso", back_populates="ordenes")
