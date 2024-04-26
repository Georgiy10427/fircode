import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fircode.startup import initialize_database, database_setup


app: FastAPI = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")

initialize_database(app)
app.router.on_startup.append(database_setup)


@app.get("/")
def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def start():
    """Launch uvicorn application"""
    uvicorn.run("fircode.main:app", host="127.0.0.1", port=8000, reload=True)
