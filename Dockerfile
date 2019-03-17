FROM ubuntu:18.04
FROM python:latest

EXPOSE 6543/tcp

RUN apt-get update -y && \
    apt-get install -y python-dev python3-pip python3-dev && \
    pip3 install --upgrade pip setuptools

# We copy this file first to leverage docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

RUN python setup.py install

RUN initialize_pyracms_db production.ini

ENTRYPOINT [ "pserve" ]

CMD [ "production.ini" ]

