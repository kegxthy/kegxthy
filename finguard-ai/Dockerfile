FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home finguard
COPY . .
RUN mkdir -p /app/data && chown -R finguard:finguard /app
USER finguard
ENV PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","7860","--workers","1"]
