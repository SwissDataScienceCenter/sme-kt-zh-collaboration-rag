FROM ghcr.io/swissdatasciencecenter/renku/py-basic-jupyterlab:2.13.2

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
      zstd curl python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY pyproject.toml /app/
COPY data_vs.db /app/data_vs.db
COPY src /app/

USER renku
