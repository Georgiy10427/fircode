from dotenv import load_dotenv
import os
from datetime import timedelta


debug = str(os.environ.get("debug", "True")).capitalize() == "True"

if debug:
    load_dotenv(".env")


# Session settings
bcrypt_rounds: int = int(os.environ.get("BCRYPT_ROUNDS", 15))
session_token_lenght: int = int(os.environ.get("SESSION_TOKEN_LENGHT", 230))
session_max_time: timedelta = timedelta(
        days=int(os.environ.get("SESSION_TIME", 30))
)
admin_email = os.environ.get("ADMIN_USERNAME", "admin@example.com")
admin_password = os.environ.get("ADMIN_PASSWORD", "admin")


# Database settings
sqlite_mode = os.environ.get("USE_SQLITE", "True").capitalize() == str(True)

# Ignored in sqlite mode
tortoise_config: dict = \
{
    'connections': {
        'master': {
            'engine': os.environ.get("DB_ENGINE", "tortoise.backends.asyncpg"),
            'credentials': {
                'host': os.environ["DB_HOST"],
                'port': os.environ.get("DB_PORT", 5432),
                'user': os.environ["DB_USER"],
                'password': os.environ["DB_PASSWORD"],
                'database': os.environ["DB_NAME"],
            }
        },
    },
    'apps': {
        'shelter': {
            'models': ['fircode.models'],
            'default_connection': 'master',
        }
    },
    'use_tz': False,
    'timezone': 'UTC'
}


