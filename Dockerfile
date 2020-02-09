FROM ubuntu:trusty
ARG VERSION=master

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y make unrar-free autoconf automake libtool gcc g++ gperf \
    flex bison texinfo gawk ncurses-dev libexpat-dev python-dev python python-serial \
    sed git unzip bash help2man wget bzip2

RUN apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && useradd --no-create-home micropython

RUN git clone --recursive https://github.com/pfalcon/esp-open-sdk.git \
  && git clone https://github.com/micropython/micropython.git \
  && cd micropython && git checkout $VERSION && git submodule update --init \
  && chown -R micropython:micropython ../esp-open-sdk ../micropython

USER micropython

RUN cd esp-open-sdk && make STANDALONE=y

ENV PATH=/esp-open-sdk/xtensa-lx106-elf/bin:$PATH

RUN cd micropython/mpy-cross && make

RUN cd micropython/ports/esp8266 && make

# This is to allow 4MB flash on NodeMCUv3
COPY extra/esp8266.ld /micropython/ports/esp8266/boards/esp8266.ld
# This will add all new frozen modules, specifically _boot.py and inisetup.py defines entrypoint
COPY src/*.py /micropython/ports/esp8266/modules

WORKDIR /micropython/ports/esp8266