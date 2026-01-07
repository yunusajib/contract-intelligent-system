FROM python:3.11-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 🔑 Fix GPG keys for old Docker
RUN apt-get update || true \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    gnupg \
    dirmngr \
    && rm -rf /var/lib/apt/lists/*

# Add Debian Bookworm keys manually
RUN set -eux; \
    mkdir -p /usr/share/keyrings; \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys \
    6ED0E7B82643E131 \
    78DBA3BC47EF2265 \
    F8D2585B8783D481 \
    54404762BBB6E853 \
    BDE6D2B9216EC7A8

# Now apt works normally
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    sqlite3 \
    libsqlite3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY agents ./agents
COPY api ./api
COPY core ./core
COPY start.py .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "start.py"]
