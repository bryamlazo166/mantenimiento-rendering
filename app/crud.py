from sqlalchemy.orm import Session
from . import models, schemas

def create_equipo(db: Session, data: schemas.EquipoCreate) -> models.Equipo:
    obj = models.Equipo(**data.model_dump(exclude={"atributos"}))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    
    # Agregar atributos
    for attr in data.atributos:
        val = models.ValorAtributoEquipo(
            equipo_id=obj.id,
            atributo_id=attr.atributo_id,
            valor_texto=attr.valor_texto,
            valor_numero=attr.valor_numero
        )
        db.add(val)
    db.commit()
    db.refresh(obj)
    return obj

def get_equipos(db: Session, skip: int = 0, limit: int = 50):
    return db.query(models.Equipo).filter(models.Equipo.activo == True).offset(skip).limit(limit).all()

def get_equipo_by_id(db: Session, equipo_id: int):
    return db.query(models.Equipo).filter(models.Equipo.id == equipo_id).first()
