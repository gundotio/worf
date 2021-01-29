FROM python:3.8.7-slim-buster

RUN apt-get update -y && \
    apt-get install -y git && \
    pip3 install glances

WORKDIR /app

#COPY Pipfile Pipfile
#COPY Pipfile.lock Pipfile.lock
RUN pip3 install pipenv

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
 
#RUN pipenv install --dev --deploy --python 3.8.7
