# Dockerfile
FROM ubuntu:22.04

# 设置非交互模式，避免 tzdata 等弹窗
ENV DEBIAN_FRONTEND=noninteractive

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
        # matplotlib 依赖（用于 PNG、字体渲染等）
        libfreetype6-dev \
        libpng-dev \
        libxft-dev \
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

# 默认工作目录
WORKDIR /src