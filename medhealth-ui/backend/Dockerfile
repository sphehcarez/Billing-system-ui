FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --retries 10 -r requirements.txt

COPY . .

EXPOSE 8001

RUN chmod +x /app/docker-entrypoint.sh

CMD ["/app/docker-entrypoint.sh"]
