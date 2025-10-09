FROM python:3.12.4-slim-bookworm

WORKDIR /app

COPY app/. .

# Instalar dependencias del sistema necesarias para MariaDB y pyarrow
RUN apt-get update -y && \
    apt-get install -y build-essential libmariadb-dev gcc \
                       libssl-dev libbz2-dev liblzma-dev zlib1g-dev \
                       libzstd-dev libsnappy-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-u", "./app.py"]
