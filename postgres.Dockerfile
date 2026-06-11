FROM postgres:16-alpine

ARG PGVECTOR_VERSION=0.8.1

RUN apk add --no-cache --virtual .build-deps build-base clang19 curl llvm19 \
    && curl -L "https://github.com/pgvector/pgvector/archive/refs/tags/v${PGVECTOR_VERSION}.tar.gz" \
        -o /tmp/pgvector.tar.gz \
    && tar -xzf /tmp/pgvector.tar.gz -C /tmp \
    && cd "/tmp/pgvector-${PGVECTOR_VERSION}" \
    && make \
    && make install \
    && apk del .build-deps \
    && rm -rf /tmp/pgvector*
