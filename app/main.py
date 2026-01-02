from fastapi.staticfiles import StaticFiles

# ... después de crear app = FastAPI(...)

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Redirigir raíz a index.html
@app.get("/")
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")
