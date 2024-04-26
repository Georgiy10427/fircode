from fircode import config
import bcrypt
from fircode.models import User
from fircode.exceptions import UserAlreadyExists
from tortoise.exceptions import DoesNotExist


async def is_user_exists(email: str) -> bool:
    """Returns true, if an user exists"""
    try:
        await User.get(email=email)
        return True
    except DoesNotExist:
        return False


async def create_user(
        email: str,
        password: str,
        first_name: str,
        second_name: str,
        is_admin=False,
        contribution=0
    ) -> None:
    """Create a new account for an user"""
    salt: bytes = bcrypt.gensalt(config.bcrypt_rounds)
    hashed_password: bytes = bcrypt.hashpw(bytes(password, "utf-8"), salt)
    if await is_user_exists(email=email):
        raise UserAlreadyExists
    else:
        await User.create(
            email=email,
            hashed_password=hashed_password.decode("utf-8"),
            first_name=first_name,
            second_name=second_name,
            contribution=contribution,
            is_admin=is_admin
        )


async def change_user_password(email: str, new_password: str) -> None:
    """Change an admin password without an old password check"""
    salt: bytes = bcrypt.gensalt(config.bcrypt_rounds)
    new_hashed_password: bytes = bcrypt.hashpw(bytes(new_password, "utf-8"), salt)
    await User.filter(email=email).update(password_hash=str(new_hashed_password))


async def delete_user(email: str) -> None:
    """Delete an user account"""
    await User.filter(email=email).delete()

