FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core fonts-noto-cjk && rm -rf /var/lib/apt/lists/*
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","7860"]
