# Dockerfile
FROM ubuntu:22.04

# 安装依赖
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        build-essential \
        python3 \
        python3-pip \
        git \
        wget \
        clang \
        libtool-bin \
        automake \
        pkg-config \
        && rm -rf /var/lib/apt/lists/*

RUN pip3 install sysv_ipc

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