FROM python:3.12.4-slim-bookworm

WORKDIR /app

# Copiar todo lo que esté en la carpeta app
COPY app/. .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando por defecto
CMD ["python", "-u", "app.py"]

