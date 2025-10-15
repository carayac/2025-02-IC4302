FROM python:3.12.4-slim-bookworm

WORKDIR /app

RUN apt-get update -y && \
    apt-get install -y build-essential libmariadb-dev gcc && \
    rm -rf /var/lib/apt/lists/*
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/. .


RUN python -u test.py

CMD [ "python", "-u", "./app.py" ]
