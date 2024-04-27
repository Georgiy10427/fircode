from fircode.models import User, SessionToken, SignInRequest
from bcrypt import checkpw
import secrets
from fastapi import Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fircode.config import session_token_lenght
from tortoise.exceptions import DoesNotExist
from fircode.config import debug
from typing import Union, Optional
import datetime
from fircode.config import session_max_time


session_responses = {
    401: {"description": "Authorization error. See detail->type"}
}


class Session:
    user: User
    token: str

    def __init__(self, token = None):
        if not token is None:
            self.token = token

    async def create_session(self, request: SignInRequest) -> Union[JSONResponse | Response]:
        try:
            user = await User.get(email=request.email)
        except DoesNotExist:
            return JSONResponse(
                status_code=401,
                content=
                {
                    "detail": {
                        "msg": "Wrong username or password",
                        "type": "auth_error.invalid_credentials"
                    }
                })

        if checkpw(request.password.encode("utf-8"), user.hashed_password.encode("utf-8")):
            token = secrets.token_urlsafe(session_token_lenght)
            self.user = user
            self.token = token
            await SessionToken.create(token=token, user=user)
            response = Response()
            expired_date = datetime.datetime.now(datetime.timezone.utc) + session_max_time
            if debug:
                response.set_cookie(key="session", value=token, expires=expired_date, httponly=False)
            else:
                response.set_cookie(key="session", value=token, expires=expired_date, samesite="strict", httponly=True)
            return response
        else:
            return JSONResponse(
                status_code=401,
                content=
                {
                    "detail": {
                        "msg": "Wrong username or password",
                        "type": "auth_error.invalid_credentials"
                    }
                })

    async def get_from_request(self, request: Request) -> None:
        if "session" in request.cookies:
            try:
                src_token = request.cookies["session"]
                token = await SessionToken.get(token=src_token)
                self.user = token.user
                self.token = src_token
            except DoesNotExist:
                raise HTTPException(status_code=401, detail="Invalid token")

        else:
            raise HTTPException(status_code=401, detail="Empty token")

    @staticmethod
    async def close_session(request: Request) -> Response:
        response = Response()
        if "session" in request.cookies:
            try:
                await SessionToken.filter(token=request.cookies["session"]).delete()
                response.delete_cookie("session")
            except DoesNotExist:
                pass
        return response
