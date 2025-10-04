FROM python:3.12.4-slim-bookworm

WORKDIR /app

# Copiar el código
COPY app/. .

# Instalar dependencias del sistema necesarias para MariaDB y compilación
RUN apt-get update -y && \
    apt-get install -y build-essential libmariadb-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando por defecto
CMD ["python", "-u", "./app.py"]