FROM python:3.8.12-buster

RUN apt-get update -y && \
    apt-get install -y git && \
    pip3 install glances

WORKDIR /app

RUN pip3 install pipenv==2020.11.15

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
COPY setup.py setup.py
COPY worf/ worf/

RUN pipenv install --dev --deploy --python 3.8.12
