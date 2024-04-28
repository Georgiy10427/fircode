FROM python:3

EXPOSE 443/tcp

WORKDIR /app

COPY . /app

RUN pip install pipx

RUN pipx install poetry

RUN apt update

RUN apt install postgresql-client -y

RUN poetry install

CMD uvicorn --workers 2 --host 0.0.0.0 --port 443 --forwarded-allow-ips="127.0.0.1" --ssl-keyfile=$ssl_keyfile --ssl-certfile=$ssl_certfile --proxy-headers fircode.main:app
