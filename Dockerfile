FROM python:3.14.6-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system app \
    && adduser --system --group app \
    && chown -R app:app /app

USER app

ENV FLASK_CONFIG=production
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "run:app"]
