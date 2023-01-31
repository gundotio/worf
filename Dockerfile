FROM python:3.10.9-buster

RUN apt-get update -y && \
    apt-get install -y git && \
    pip3 install glances

WORKDIR /app

RUN pip3 install poetry

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY worf/ worf/

RUN poetry install
