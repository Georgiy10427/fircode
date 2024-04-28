from typing import List

import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction

from fircode import config
from fircode.exceptions import UserAlreadyExists
from fircode.models import *
from fircode.session import Session, session_responses
from fircode.spa_static_files import SinglePageApplication
from fircode.startup import initialize_database, database_setup
from fircode.user_utils import create_user

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
            phone=new_user.phone_number,
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


@api_app.get("/users_stat", response_model=List[UserResponseForStat])
async def get_users_stat():
    """Provide information about users"""
    """Exclude fields email, phone and is_admin from response"""
    return await UserResponseForStat.from_queryset(User.all().order_by("-contribution"))


@api_app.post("/logout")
async def logout(request: Request):
    """Logout from current user"""
    return await Session().close_session(request)


@api_app.get("/dogs", response_model=List[DogOut])
async def get_all_dogs():
    """Provide list of all dogs"""
    return await DogOut.from_queryset(Dog.all().order_by("feed_amount"))


@api_app.get("/dog/{dog_id}")
async def get_dog_by_id(dog_id: int):
    """Provide full information about dog by id"""
    try:
        return await DogOut.from_queryset_single(Dog.get(id=dog_id))
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
async def update_dog(request: Request, new_instance: DogUpdateIn):
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
        return JSONResponse(status_code=405, content="You doesn't have permissions to update dog")


@api_app.delete("/dog/{dog_id}")
async def delete_dog(request: Request, dog_id: int):
    """Delete dog from shelter"""
    session = Session()
    await session.get_from_request(request)
    if session.user.is_admin:
        await Dog.filter(id=dog_id).delete()
    else:
        return JSONResponse(status_code=405, content="You doesn't have permissions to delete dog")


@api_app.get("/feed_requests", response_model=List[FeedRequestResponse])
async def get_users_feed_requests():
    """Provide all feed requests from users"""
    return await FeedRequestResponse.from_queryset(FeedRequest.all().order_by("arrived_at"))


@api_app.get("/feed_requests/current", response_model=List[FeedRequestResponse])
async def get_user_feed_requests(request: Request):
    """Provide all feed requests from current user"""
    session = Session()
    await session.get_from_request(request)
    current_user = await User.get(email=session.user.email)
    return await FeedRequestResponse.from_queryset(FeedRequest.filter(actor=current_user).order_by("arrived_at"))


@api_app.post("/feed_request")
async def add_feed_request(request: Request, feed_request: FeedRequestIn):
    """Add feed request to order"""
    session = Session()
    await session.get_from_request(request)
    current_user = await User.get(email=session.user.email)
    if feed_request.feed_amount <= 0:
        return JSONResponse(status_code=422, content="You can't send empty donates")
    target_dog = await Dog.get(id=feed_request.target_id)
    data = feed_request.model_dump(exclude={"target_id"})
    feed_request = FeedRequest(**data, actor=current_user, target=target_dog)
    await feed_request.save()
    return feed_request


@api_app.post("/feed_requests/approve")
async def approve_feed_request(request: Request, approve_request: FeedRequestApproveRequest):
    """Approve or decline the feed request (admin only)"""
    session = Session()
    await session.get_from_request(request)
    if session.user.is_admin:
        try:
            feed_request = await FeedRequest.get(id=approve_request.id)
        except DoesNotExist:
            return JSONResponse(status_code=404, content="Feed request with this id doesn't exist")
        await feed_request.fetch_related("target")
        await feed_request.fetch_related("actor")
        if approve_request.approved:
            async with in_transaction():
                await User.filter(email=feed_request.actor.email).update(
                    contribution=feed_request.actor.contribution + approve_request.award)
                await Dog.filter(id=feed_request.target.id).update(
                    feed_amount=feed_request.target.feed_amount + feed_request.feed_amount)
        await feed_request.delete()
    else:
        return JSONResponse(status_code=405, content="You doesn't have permissions to approve food requests")


@api_app.delete("/feed_requests/{request_id}")
async def delete_user_feed_request(request: Request, request_id: int):
    """Delete user feed request (by himself)"""
    session = Session()
    await session.get_from_request(request)
    current_user = await User.get(email=session.user.email)
    feed_request = await FeedRequest.filter(actor=current_user, id=request_id).get_or_none()
    if feed_request is None:
        return JSONResponse(status_code=404, content="You feed request doesn't found")
    else:
        await feed_request.delete()


def start():
    """Launch uvicorn application"""
    uvicorn.run("fircode.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == '__main__':
    start()
