FROM python:3.12.4-slim-bookworm

WORKDIR /app

# archivo de dependencias
COPY app/requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

#copiar el resto del código
COPY app/. .

# ejecutar la aplicación
CMD ["python", "app.py"]