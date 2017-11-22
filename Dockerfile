FROM ubuntu:xenial
MAINTAINER Krishna Dubba <krishna.dubba@gmail.com>

RUN sed -i 's/archive.ubuntu.com/mirror.us.leaseweb.net/' /etc/apt/sources.list \
        && sed -i 's/deb-src/#deb-src/' /etc/apt/sources.list \
        && apt-get update \
        && apt-get upgrade -y \
        && apt-get install -y \
        build-essential \
        ca-certificates \
        gcc \
        git \
        wget \
        software-properties-common \
        libpq-dev \
        make \
        pkg-config \
        python3 \
        python3-dev \
        python3-pip \
        aria2 \
        libjpeg8-dev \
        zlib1g-dev \
        && apt-get autoremove -y \ 
        && apt-get clean
        
RUN wget -qO - http://packages.confluent.io/deb/3.3/archive.key | apt-key add -
RUN add-apt-repository "deb [arch=amd64] http://packages.confluent.io/deb/3.3 stable main"
RUN apt-get update
RUN apt-get install -y librdkafka1 librdkafka-dev

ENV INSTALL_PATH /uggipuggi
RUN mkdir -p $INSTALL_PATH

WORKDIR $INSTALL_PATH

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . .
EXPOSE 8000
CMD gunicorn -b 0.0.0.0:8000 --access-logfile - "manage:uggipuggi.app"
