FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget gcc libffi-dev musl-dev ffmpeg aria2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r Installer

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV COOKIES_FILE_PATH="/app/youtube_cookies.txt"

CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8000} & python3 modules/main.py
