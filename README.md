# Ёлкин код
## Installation (CLI)
0. [Install Poetry](https://python-poetry.org/docs/#installation)
1. Clone this repository and go into this one in a console
2. Install dependencies: `poetry install`
3. Setup Postgres or add `USE_SQLITE = "False"` to `.env`
4. Run server (in the root of this repo): `poetry run start`

## Installation (Pycharm)
0. [Install Poetry](https://python-poetry.org/docs/#installation)
1. Clone this repository and open it into the IDE
2. Pycharm will suggest you to resolve dependencies with Poetry. You need to agree.
3. Setup Postgres or add `USE_SQLITE = "False"` to `.env`
4. Setup FastAPI configuration like that:
![Pycharm configuration](pycharm_setup.png)
