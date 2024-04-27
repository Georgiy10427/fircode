import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fircode.startup import initialize_database, database_setup
from fircode.models import UserRegistrationRequest
from fircode.user_utils import create_user
from fircode.exceptions import UserAlreadyExists
from fastapi.exceptions import HTTPException


app: FastAPI = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")

initialize_database(app)
app.router.on_startup.append(database_setup)


@app.get("/")
def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/registration")
async def user_registration(new_user: UserRegistrationRequest):
    try:
        await create_user(
            email=new_user.email,
            password=new_user.password,
            first_name=new_user.first_name,
            second_name=new_user.second_name,
            is_admin=False
        )
    except UserAlreadyExists:
        raise HTTPException(
            status_code=409,
            detail="User already exists"
        )


def start():
    """Launch uvicorn application"""
    uvicorn.run("fircode.main:app", host="127.0.0.1", port=8000, reload=True)
