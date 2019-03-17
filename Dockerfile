FROM ubuntu:18.04

RUN apt-get update -y && \
    apt-get install -y python3.7 python3-pip python3-dev && \
    pip3 install --upgrade pip setuptools

# We copy this file first to leverage docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3.7 install -r requirements.txt

COPY . /app

ENTRYPOINT [ "waitress" ]

CMD [ "development.ini" ]

