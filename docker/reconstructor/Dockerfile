FROM neural-networks-base AS dev

WORKDIR /app/docker/reconstructor

ENV UV_TOOLS_ENVIRONMENT=/opt/uv/tools

COPY docker/reconstructor/pylock.toml ./pylock.toml
RUN --mount=type=cache,id=uvcache,sharing=locked,target=/root/.cache/uv \
    uv pip install -r pylock.toml

COPY packages/python/core /app/packages/python/core
COPY packages/python/common /app/packages/python/common
COPY packages/generated/python/api-client /app/packages/generated/python/api-client
COPY docker/reconstructor /app/docker/reconstructor
RUN uv pip install --no-deps --no-sources \
    /app/packages/python/common \
    /app/packages/python/core \
    /app/packages/generated/python/api-client \
    /app/docker/reconstructor

RUN uv pip check

COPY --chmod=0755 docker/reconstructor/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
