FROM python:3.12
# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# chemin interne container
WORKDIR /app

# install dependances uv
COPY pyproject.toml uv.lock /app/
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"
RUN uv sync --locked --no-dev

# copier le code source de l'ordinateur vers container et recrer arborescence dans container
COPY src/ ./src/

# Ouvrir les port streamlit fastapi
EXPOSE 8000 8501