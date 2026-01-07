# Dockerfile
FROM ubuntu:22.04

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        python3 \
        python3-pip \
        python3-dev \
        git \
        wget \
        clang \
        libtool-bin \
        automake \
        pkg-config \
        autoconf cmake \
        # matplotlib 依赖（用于 PNG、字体渲染等）
        libfreetype6-dev \
        libpng-dev \
        libxft-dev \
        # tcpdump 依赖
        libpcap-dev \
        sudo \
        && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip3 install --no-cache-dir \
        sysv_ipc \
        matplotlib

# 编译并安装 AFL++
WORKDIR /root
RUN git clone https://github.com/AFLplusplus/AFLplusplus.git && \
    cd AFLplusplus && \
    make distrib && \
    make install

# 设置 PATH
ENV PATH="/usr/local/bin:${PATH}"

# 创建非 root 用户（UID/GID 通过构建参数传入）
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} fuzzer && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -m -s /bin/bash fuzzer && \
    echo "fuzzer ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# 切换到非 root 用户
USER fuzzer

# 默认工作目录
WORKDIR /src