import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fircode.startup import initialize_database, database_setup
from fircode.models import UserRegistrationRequest, SignInRequest, UserResponse
from fircode.user_utils import create_user
from fircode.exceptions import UserAlreadyExists
from fastapi.exceptions import HTTPException
from fircode import config
from fastapi.middleware.cors import CORSMiddleware
from fircode.session import Session, session_responses


app: FastAPI = FastAPI(title="root app")
api_app: FastAPI = FastAPI(title="api app")

app.mount("/api", api_app)
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if config.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    api_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

initialize_database(app)
app.router.on_startup.append(database_setup)


@api_app.post("/registration")
async def user_registration(new_user: UserRegistrationRequest):
    """Provide user registration"""
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


@api_app.post("/login", responses=session_responses)
async def login(request: SignInRequest):
    """Login into user account via password and email"""
    return await Session().create_session(request)


@api_app.get("/user", responses=session_responses, response_model=UserResponse)
async def current_user(request: Request):
    session = Session()
    await session.get_from_request(request)
    return await UserResponse.from_queryset_single(session.user.get())


@api_app.post("/logout")
async def logout(request: Request):
    return await Session().close_session(request)


def start():
    """Launch uvicorn application"""
    uvicorn.run("fircode.main:app", host="127.0.0.1", port=8000, reload=True)
