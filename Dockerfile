FROM sgoblin/python3.5
MAINTAINER Krishna Dubba <krishna.dubba@gmail.com>

RUN apt-get install -y wget
RUN apt-get install -y software-properties-common
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
RUN pip3 install --editable .

CMD gunicorn -b 0.0.0.0:8000 --access-logfile - "manage:uggipuggi.app"
