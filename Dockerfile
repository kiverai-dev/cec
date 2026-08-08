FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y unrar-free fonts-dejavu-core tesseract-ocr tesseract-ocr-rus && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN mkdir -p /app/data/uploads /app/data/results /app/data/db /app/data/models

COPY app/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONPATH=/app

EXPOSE 8501

ENTRYPOINT ["/entrypoint.sh"]
