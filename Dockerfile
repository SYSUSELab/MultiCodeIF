FROM python:3.9-slim

WORKDIR /workspace

ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.cargo/bin:/root/.local/bin:/root/.sdkman/candidates/kotlin/current/bin:${PATH}"
ENV DEBIAN_FRONTEND=noninteractive

RUN cd /etc/apt/sources.list.d \
    && cp debian.sources debian.sources.bak \
    && sed -i 's@deb.debian.org@repo.huaweicloud.com@g' debian.sources \
    && sed -i 's@security.debian.org@repo.huaweicloud.com@g' debian.sources

RUN apt-get update && apt-get install -y \
    git \
    vim \
    curl \
    wget \
    build-essential \
    default-jdk \
    nodejs \
    npm \
    gcc \
    g++ \
    mono-mcs \
    zip \
    unzip \
    swi-prolog \
    lua5.4 \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && . "$HOME/.cargo/env"

RUN apt-get update && apt-get install -y golang && rm -rf /var/lib/apt/lists/*

RUN npm install -g typescript

RUN npm install -g coffeescript

RUN curl -s "https://get.sdkman.io" | bash \
    && bash -c "source $HOME/.sdkman/bin/sdkman-init.sh && sdk install kotlin"

RUN curl --proto '=https' --tlsv1.2 -sSf https://get-ghcup.haskell.org | sh

RUN curl -fsSL https://install.julialang.org | sh -s -- -y

COPY requirements.txt* ./

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi \
    && pip install --no-cache-dir guesslang

RUN pip uninstall typing_extensions -y

RUN pip install --no-cache-dir typing_extensions

RUN echo 'source "$HOME/.cargo/env"' >> ~/.bashrc \
    && echo 'source "$HOME/.sdkman/bin/sdkman-init.sh"' >> ~/.bashrc

CMD ["/bin/bash"]