FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG RUBY_VERSION=3.1.6
ARG BUNDLER_VERSION=2.6.9

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    curl \
    gpg \
    libyaml-dev \
    zlib1g-dev \
    libffi-dev \
    libgdbm-dev \
    libreadline-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libheif-examples \
    ffmpeg \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
  && mkdir -p -m 755 /etc/apt/keyrings \
  && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | gpg --dearmor -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
  && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends gh \
  && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/rbenv/rbenv.git /usr/local/rbenv \
  && git clone https://github.com/rbenv/ruby-build.git /usr/local/rbenv/plugins/ruby-build

ENV RBENV_ROOT=/usr/local/rbenv
ENV PATH=/usr/local/rbenv/bin:/usr/local/rbenv/shims:$PATH

RUN /usr/local/rbenv/bin/rbenv install ${RUBY_VERSION} \
  && /usr/local/rbenv/bin/rbenv global ${RUBY_VERSION} \
  && gem install bundler:${BUNDLER_VERSION} \
  && gem install ruby-lsp
