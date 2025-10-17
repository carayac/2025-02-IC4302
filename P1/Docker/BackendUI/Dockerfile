FROM python:3.12.4-slim-bookworm

WORKDIR /app

# install dependencies to build mariadb connector 
RUN apt-get update && apt-get install -y \
    libmariadb-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# copy only requirements to cache dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of the application
COPY app/. .

EXPOSE 5000

RUN python -u test.py

CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
