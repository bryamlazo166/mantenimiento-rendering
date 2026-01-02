

# ============ CLASES DE EQUIPO ============

@app.post("/clases/", response_model=schemas.ClaseEquipoOut)
def crear_clase_equipo(data: schemas.ClaseEquipoCreate, db: Session = Depends(get_db)):
    return crud.create_clase_equipo(db, data)

@app.get("/clases/", response_model=list[schemas.ClaseEquipoOut])
def listar_clases_equipo(db: Session = Depends(get_db)):
    return crud.get_clases_equipo(db)


# ============ ATRIBUTOS DE CLASE ============

@app.post("/atributos/", response_model=schemas.AtributoClaseOut)
def crear_atributo_clase(data: schemas.AtributoClaseCreate, db: Session = Depends(get_db)):
    return crud.create_atributo_clase(db, data)

@app.get("/atributos/{clase_id}", response_model=list[schemas.AtributoClaseOut])
def listar_atributos_clase(clase_id: int, db: Session = Depends(get_db)):
    return crud.get_atributos_by_clase(db, clase_id)


# ============ AVISOS ============

@app.post("/avisos/", response_model=schemas.AvisoOut)
def crear_aviso(data: schemas.AvisoCreate, db: Session = Depends(get_db)):
    return crud.create_aviso(db, data)

@app.get("/avisos/", response_model=list[schemas.AvisoOut])
def listar_avisos(equipo_id: int = None, db: Session = Depends(get_db)):
    return crud.get_avisos(db, equipo_id=equipo_id)

@app.get("/avisos/{aviso_id}", response_model=schemas.AvisoOut)
def obtener_aviso(aviso_id: int, db: Session = Depends(get_db)):
    aviso = crud.get_aviso_by_id(db, aviso_id)
    if not aviso:
        raise HTTPException(status_code=404, detail="Aviso no encontrado")
    return aviso


# ============ ÓRDENES DE TRABAJO ============

@app.post("/ordenes/", response_model=schemas.OrdenTrabajoOut)
def crear_orden_trabajo(data: schemas.OrdenTrabajoCreate, db: Session = Depends(get_db)):
    return crud.create_orden_trabajo(db, data)

@app.get("/ordenes/", response_model=list[schemas.OrdenTrabajoOut])
def listar_ordenes_trabajo(aviso_id: int = None, db: Session = Depends(get_db)):
    return crud.get_ordenes_trabajo(db, aviso_id=aviso_id)

@app.get("/ordenes/{orden_id}", response_model=schemas.OrdenTrabajoOut)
def obtener_orden_trabajo(orden_id: int, db: Session = Depends(get_db)):
    orden = crud.get_orden_by_id(db, orden_id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    return orden

@app.put("/ordenes/{orden_id}", response_model=schemas.OrdenTrabajoOut)
def actualizar_orden_trabajo(orden_id: int, data: schemas.OrdenTrabajoUpdate, db: Session = Depends(get_db)):
    orden = crud.get_orden_by_id(db, orden_id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de trabajo no encontrada")
    return crud.update_orden_trabajo(db, orden, data)
