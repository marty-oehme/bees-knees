FROM python:3.13-slim-bookworm AS build

SHELL ["sh", "-exc"]

ENV DEBIAN_FRONTEND=noninteractive

RUN <<EOT
apt-get update -qy
apt-get install -qyy \
    build-essential \
    ca-certificates \
    python3-setuptools \
EOT

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# no warnings about missing hardlinking
ENV UV_LINK_MODE=copy \
    # bytecode compilation for fast startup
    UV_COMPILE_BYTECODE=1 \
    # don't download isolated python setups
    UV_PYTHON_DOWNLOADS=never \
    # stick to debian available
    UV_PYTHON=python3.13 \
    # set our working env
    UV_PROJECT_ENVIRONMENT=/app

## END of build prepping

# sync all DEPENDENCIES (without actual application)
RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync \
    --locked \
    --no-dev \
    --no-install-project

# sync app itself
COPY . /src
WORKDIR /src
RUN --mount=type=cache,target=/root/.cache \
    uv sync \
    --locked \
    --no-dev \
    --no-editable

############################ APP CONTAINER ############################

FROM python:3.13-slim-bookworm
SHELL ["sh", "-exc"]

ENV PATH=/app/bin:$PATH

# run app rootless
RUN <<EOT
groupadd -r app
useradd -r -d /app -g app -N app
EOT

ENTRYPOINT ["tini", "-v", "--", "prophet"]
STOPSIGNAL SIGINT

RUN <<EOT
apt-get update -qy
apt-get install -qyy \
    python3.11 \
    libpython3.11 \
    tini

apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOT

COPY --from=build --chown=app:app /app /app
COPY --from=build --chown=app:app /src/static /app/static
COPY --from=build --chown=app:app /src/templates /app/templates

USER app
WORKDIR /app

RUN <<EOT
python -V
python -Im site
python -Ic 'import prophet'
EOT
