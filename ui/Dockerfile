FROM python:3.13-slim

WORKDIR /app

RUN apt-get update -y \
    && apt-get install -y \
        gcc \
        curl \
        git \
        unzip \
        jq \
        python3-dev \
        libpq-dev \
        && apt-get -y clean 

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev dependencies)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY streamlit_app.py config.yaml ./
COPY pages/ pages/
COPY config.py storage.py diff_csv.py misc.py s3_and_local_files.py ./

# Expose Streamlit default port
EXPOSE 8501

# Run Streamlit
CMD ["uv", "run", "streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
