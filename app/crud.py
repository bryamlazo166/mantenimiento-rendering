
# ============ CLASES Y ATRIBUTOS ============

def create_clase_equipo(db: Session, data: schemas.ClaseEquipoCreate):
    obj = models.ClaseEquipo(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_clases_equipo(db: Session):
    return db.query(models.ClaseEquipo).all()

def create_atributo_clase(db: Session, data: schemas.AtributoClaseCreate):
    obj = models.AtributoClase(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_atributos_by_clase(db: Session, clase_id: int):
    return db.query(models.AtributoClase).filter(models.AtributoClase.clase_id == clase_id).all()


# ============ AVISOS ============

def create_aviso(db: Session, data: schemas.AvisoCreate):
    obj = models.Aviso(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_avisos(db: Session, equipo_id: int = None):
    q = db.query(models.Aviso)
    if equipo_id:
        q = q.filter(models.Aviso.equipo_id == equipo_id)
    return q.all()

def get_aviso_by_id(db: Session, aviso_id: int):
    return db.query(models.Aviso).filter(models.Aviso.id == aviso_id).first()


# ============ ÓRDENES DE TRABAJO ============

def create_orden_trabajo(db: Session, data: schemas.OrdenTrabajoCreate):
    obj = models.OrdenTrabajo(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_ordenes_trabajo(db: Session, aviso_id: int = None):
    q = db.query(models.OrdenTrabajo)
    if aviso_id:
        q = q.filter(models.OrdenTrabajo.aviso_id == aviso_id)
    return q.all()

def get_orden_by_id(db: Session, orden_id: int):
    return db.query(models.OrdenTrabajo).filter(models.OrdenTrabajo.id == orden_id).first()

def update_orden_trabajo(db: Session, orden: models.OrdenTrabajo, data: schemas.OrdenTrabajoUpdate):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(orden, field, value)
    db.commit()
    db.refresh(orden)
    return orden
