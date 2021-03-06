FROM python:3.8.8-slim-buster

RUN apt-get update -y && \
    apt-get install -y git && \
    pip3 install glances

WORKDIR /app

RUN pip3 install pipenv

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --dev --deploy --python 3.8.8
