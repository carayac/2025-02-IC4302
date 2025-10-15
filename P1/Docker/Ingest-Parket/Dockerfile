FROM python:3.12.4-slim-bookworm

WORKDIR /app

# Instalar dependencias del sistema necesarias para MariaDB y compilación
RUN apt-get update -y && \
    apt-get install -y build-essential libmariadb-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# copy only requirements to cache dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the application
COPY app/. .

# Comando por defecto
CMD ["python", "-u", "./app.py"]
