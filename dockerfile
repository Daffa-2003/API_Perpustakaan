FROM python:3.11

WORKDIR /Digital-Library

COPY .. /Digital-Library/

RUN python -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 8770

ENV FLASK_APP=app.py

CMD [ "flask", "run", "--host=0.0.0.0"]
