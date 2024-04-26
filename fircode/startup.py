from fircode import config
from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI
from fastapi.logger import logger
from fircode import user_utils
from fircode.exceptions import UserAlreadyExists


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
