# Dockerfile
FROM ubuntu

# 安装系统依赖
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        # Python
        python3 \
        python3-pip \
        python3-dev \
        # 必需依赖
        build-essential \
        clang \
        llvm \
        libtool-bin \
        cmake \
        file \
        binutils \
        git \
        # 项目构建工具（部分目标需要）
        automake \
        autoconf \
        pkg-config \
        # matplotlib 图形库依赖
        libfreetype6-dev \
        libpng-dev \
        libxft-dev \
        # tcpdump 依赖
        libpcap-dev \
        && rm -rf /var/lib/apt/lists/*


# 安装 Python 依赖
RUN pip3 install --no-cache-dir --break-system-packages \
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