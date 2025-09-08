FROM python:3.11-slim

# System deps (optional but helpful for pandas/yfinance)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only project metadata first to leverage caching
COPY pyproject.toml README.md CODE_GUIDE.md /app/
COPY src /app/src
COPY sample /app/sample

# Install project
RUN pip install --no-cache-dir .

# Default command: show help
ENTRYPOINT ["value-screener"]
CMD ["--help"]
