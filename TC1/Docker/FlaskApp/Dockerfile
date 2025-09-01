FROM python:3.12.4-slim-bookworm

WORKDIR /app

COPY app/. .
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto de Flask para que pueda ser accesible desde fuera del contenedor
EXPOSE 5000

CMD [ "flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000" ]