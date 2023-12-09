FROM python:3.10
WORKDIR /bots
COPY config.txt config.txt
RUN pip3 install --upgrade setuptools
RUN pip3 install -r config.txt
RUN chmod 755 .
COPY . .