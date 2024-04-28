from fastapi import FastAPI
from fastapi.logger import logger
from tortoise.contrib.fastapi import register_tortoise

from fircode import config
from fircode import user_utils
from fircode.exceptions import UserAlreadyExists
from fircode.models import *


def initialize_database(app: FastAPI):
    """Initialize database (sqlite/postgres)"""
    if not config.sqlite_mode:
        register_tortoise(
            app,
            config=config.tortoise_config,
            generate_schemas=True,
            add_exception_handlers=True
        )
    else:
        register_tortoise(
            app,
            db_url="sqlite://database.sqlite3",
            modules={"shelter": ["fircode.models"]},
            generate_schemas=True,
            add_exception_handlers=True
        )


async def database_setup() -> None:
    """Pull necessary data to database on first startup"""
    """Create admin account, if it doesn't exist"""
    try:
        await user_utils.create_user(
            email=config.admin_email,
            password=config.admin_password,
            first_name="Host",
            second_name="(Admin)",
            is_admin=True
        )
        logger.info("The admin account created (see credentials in config)")
    except UserAlreadyExists:
        logger.info("The admin account already exist")

    if config.debug:
        test_user_model = None
        try:
            test_user_model = await user_utils.create_user(email="alexey@example.com", phone="+71864926326",
                                                           is_admin=False,
                                                           password="12345", contribution=2, first_name="Алексей",
                                                           second_name="Поднебесный")
            await user_utils.create_user(email="wind@example.com", phone="+72369026326", is_admin=False,
                                         password="12345", contribution=5, first_name="Снежана",
                                         second_name="Раневская")
            await user_utils.create_user(email="kafka@example.com", phone="+71864920326", is_admin=False,
                                         password="12345", contribution=1, first_name="Франц", second_name="Кафка")
        except UserAlreadyExists:
            pass

        if await Dog.all().count() == 0:
            await Dog.create(name="Шарик", age=5, description="Дружелюбный, симпатичный. Отсидел десятку",
                             gender=Gender.male, feed_amount=1, arrived_at=date(year=2024, month=4, day=30))
            await Dog.create(name="Бобик", age=7, description="Дружелюбный, симпатичный. Поймал Шарика",
                             gender=Gender.male, feed_amount=1, arrived_at=date(year=2024, month=4, day=29))
            await Dog.create(name="Маня", age=6, description="Игривая, ласковая, но строгая",
                             gender=Gender.female, feed_amount=1, arrived_at=date(year=2024, month=4, day=28),
                             host=test_user_model)
