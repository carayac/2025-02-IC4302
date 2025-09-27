FROM python:3.12.4-slim-bookworm

WORKDIR /app

# 1. Instalar dependencias del sistema (esto casi nunca cambia)
RUN apt-get update && apt-get install -y \
    libmariadb-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Copiar solo requirements.txt y hacer pip install (esto cambia a veces)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Ahora sí, copiar el resto de la app (esto cambia mucho)
COPY app/. .

EXPOSE 5000

CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
