FROM python:3.12.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/service/src

WORKDIR /service

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY requirements.txt ./
RUN python -m pip install \
    --disable-pip-version-check \
    --no-cache-dir \
    --requirement requirements.txt

COPY --chown=app:app src ./src

USER app

EXPOSE 8080

CMD ["sh", "-c", "exec gunicorn --bind \"0.0.0.0:${PORT:-8080}\" --workers 1 --threads 8 --timeout 30 --access-logfile - --error-logfile - --no-control-socket 'work_on_the_decayed.http:create_app()'"]
