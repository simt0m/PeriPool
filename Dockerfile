FROM python:3.14.6-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN addgroup --system app \
    && adduser --system --group --home /home/app app \
    && mkdir -p /home/app \
    && chown -R app:app /app /home/app

USER app

ENV HOME=/home/app
ENV FLASK_CONFIG=production
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "run:app"]
