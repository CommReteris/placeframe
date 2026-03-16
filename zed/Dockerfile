ARG ZED_BASE_IMAGE
FROM ${ZED_BASE_IMAGE}

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app/zed

ENV \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_INSTALLER_METADATA=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/uv/venv \
    VIRTUAL_ENV=/opt/uv/venv

# Stereolabs base images don't include Python 3.13
RUN uv python install 3.13

RUN uv venv $UV_PROJECT_ENVIRONMENT

# Generate pyzed wheel matching the installed ZED SDK version.
# get_python_api.py ships inside the SDK and outputs a wheel to /usr/local/zed/.
# Running under QEMU on aarch64 ensures the correct platform wheel is produced.
RUN uv run --python 3.13 /usr/local/zed/get_python_api.py
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install /usr/local/zed/pyzed*.whl

# Install remaining dependencies from lock file
COPY zed/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

# Install source packages
COPY packages/python/common /app/packages/python/common
COPY packages/python/core /app/packages/python/core
COPY zed /app/zed
RUN uv pip install --no-deps --no-sources \
    /app/packages/python/common \
    /app/packages/python/core \
    /app/zed

RUN uv pip check

COPY --chmod=0755 zed/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
