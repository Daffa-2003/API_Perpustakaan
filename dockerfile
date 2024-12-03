FROM python:3.11

WORKDIR /Digital-Library

RUN python -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8770

ENV FLASK_APP=app.py


CMD ["flask", "db", "init"] && \
    ["flask", "db", "migrate", "-m", "done"] && \
    ["flask", "db", "upgrade"] && \
    ["flask", "run", "--host=0.0.0.0"]
