FROM ghcr.io/swissdatasciencecenter/renku/py-basic-jupyterlab:2.13.2

USER root

RUN apt-get update && apt-get install -y zstd && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

USER renku
