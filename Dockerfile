# pull official base image
FROM  python:3.13.6-slim-bookworm

# set working directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1 

# Install system dependencies
RUN apt-get update \
  && apt-get -y install gcc postgresql \
  && apt-get clean

# Upgrade pip and install poetry
RUN python -m pip install --upgrade pip
RUN pip install uv
RUN export UV_HTTP_TIMEOUT=900
# Copy project files
COPY ./pyproject.toml .

# Install dependencies
RUN uv pip install -r pyproject.toml --extra dev --system

# Copy the rest of the application
COPY . .


CMD ["uvicorn", "app.backend.v1.api:app", "--host", "0.0.0.0", "--port", "4000"]
