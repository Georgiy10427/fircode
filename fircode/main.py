import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fircode.spa_static_files import SinglePageApplication
from fircode.startup import initialize_database, database_setup
from fircode.models import *
from fircode.user_utils import create_user
from fircode.exceptions import UserAlreadyExists
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fircode import config
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fircode.session import Session, session_responses
from fastapi.templating import Jinja2Templates
from tortoise.contrib.fastapi import HTTPNotFoundError
from tortoise.exceptions import DoesNotExist


app: FastAPI = FastAPI(title="root app")
api_app: FastAPI = FastAPI(title="api app")

app.mount("/api", api_app)
app.mount("/", app=SinglePageApplication(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")


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
    """Provide information about current user"""
    session = Session()
    await session.get_from_request(request)
    return session.user


@api_app.get("/user/{email}", response_model=UserResponse, responses={404: {"model": HTTPNotFoundError}})
async def get_user_by_email(email: EmailStr):
    """Provide user information by email"""
    try:
        return await UserResponse.from_queryset_single(User.get(email=email))
    except DoesNotExist:
        return JSONResponse(status_code=404, content="User with this email doesn't exist")


@api_app.get("/users_stat", response_model=List[UserResponse])
async def get_users_stat():
    """Provide information about users"""
    return await UserResponse.from_queryset(User.all().order_by("contribution"))


@api_app.post("/logout")
async def logout(request: Request):
    """Logout from current user"""
    return await Session().close_session(request)


@api_app.get("/dogs", response_model=List[DogOut])
async def get_all_dogs():
    """Provide list of all dogs"""
    return await Dog.all()


@api_app.get("/dog/{dog_id}", response_model=DogOut, responses={404: {"model": HTTPNotFoundError}})
async def get_dog_by_id(dog_id: int):
    """Provide full information about dog by id"""
    try:
        await DogOut.from_queryset_single(Dog.get(id=dog_id))
    except DoesNotExist:
        return JSONResponse(status_code=404, content="Dog with this id doesn't exist")


@api_app.post("/dog", responses={**session_responses, 405: {"Method not allowed": {}}})
async def add_dog(request: Request, new_dog: DogIn):
    """Add dog"""
    session = Session()
    await session.get_from_request(request)
    if session.user.is_admin:
        if new_dog.gender in ("male", "female"):
            dog = await Dog.create(**new_dog.dict(exclude_unset=True))
            return dog
        else:
            return JSONResponse(status_code=422, content="Gender isn't valid")
    else:
        return JSONResponse(status_code=405, content="You doesn't have permissions to add dog")


@api_app.put("/dog", responses={**session_responses, 405: {"Method not allowed": {}}})
async def update_dog(request: Request, new_instance: DogOut):
    """Update an instance of the dog"""
    session = Session()
    await session.get_from_request(request)
    if session.user.is_admin:
        if new_instance.gender in ("male", "female"):
            await Dog.filter(id=new_instance.id).update(**new_instance.model_dump(exclude={"id"}))
            return await DogOut.from_queryset_single(Dog.get(id=new_instance.id))
        else:
            return JSONResponse(status_code=422, content="Gender isn't valid")
    else:
        return JSONResponse(status_code=405, content="You doesn't have permissions to add dog")


@api_app.delete("/dog/{dog_id}")
async def delete_dog(request: Request, dog_id: int):
    """Delete dog from shelter"""
    session = Session()
    await session.get_from_request(request)
    if session.user.is_admin:
        await Dog.filter(id=dog_id).delete()
    else:
        return JSONResponse(status_code=405, content="You doesn't have permissions to delete dog")


def start():
    """Launch uvicorn application"""
    uvicorn.run("fircode.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == '__main__':
    start()