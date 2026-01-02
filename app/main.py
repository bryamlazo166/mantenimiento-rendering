from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas, crud
from .database import engine, Base
from .deps import get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestión de Mantenimiento - Beta", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API de Gestión de Mantenimiento funcionando", "version": "0.1.0"}

@app.post("/equipos/", response_model=schemas.EquipoOut)
def crear_equipo(data: schemas.EquipoCreate, db: Session = Depends(get_db)):
    return crud.create_equipo(db, data)

@app.get("/equipos/", response_model=list[schemas.EquipoOut])
def listar_equipos(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud.get_equipos(db, skip=skip, limit=limit)

@app.get("/equipos/{equipo_id}", response_model=schemas.EquipoOut)
def obtener_equipo(equipo_id: int, db: Session = Depends(get_db)):
    equipo = crud.get_equipo_by_id(db, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return equipo
