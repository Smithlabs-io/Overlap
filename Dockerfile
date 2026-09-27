# One image. The command picks the workload:
#
#   python -m overlap        the Discord bot (default)
#   python -m overlap.web    the web app
#   dbmate up                apply the database migrations
#
# All three need DATABASE_URL (dbmate wants the postgres:// form). The image keeps no local state.

FROM python:3.12-slim

ARG TARGETARCH
ARG DBMATE_VERSION=2.36.0
ADD --chmod=755 https://github.com/amacneil/dbmate/releases/download/v${DBMATE_VERSION}/dbmate-linux-${TARGETARCH} /usr/local/bin/dbmate

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DBMATE_MIGRATIONS_DIR=/app/overlap/db/migrations \
    DBMATE_NO_DUMP_SCHEMA=true

WORKDIR /app
COPY pyproject.toml ./
COPY overlap ./overlap
RUN pip install ".[bot,web]"

EXPOSE 8080
CMD ["python", "-m", "overlap"]
