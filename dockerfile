FROM python:3.11.4-alpine

RUN apk add --update libpq-dev gcc

WORKDIR /Digital-Library

COPY app.py requirements.txt /Digital-Library/

RUN python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=app.py

CMD [ "flask", "run", "--host=0.0.0.0"]
