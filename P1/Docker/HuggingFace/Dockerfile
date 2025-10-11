FROM python:3.12.4-slim-bookworm

WORKDIR /app

COPY app/requirements.txt .

RUN pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt

COPY app/. .

# RUN python -m pytest test.py -v

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2"]
