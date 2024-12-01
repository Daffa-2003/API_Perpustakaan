FROM python:3.9

WORKDIR /Digital-Library

COPY app.py requirements.txt /Digital-Library/

RUN python -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 5000

ENV FLASK_APP=app.py

CMD [ "flask", "run", "--host=0.0.0.0"]
