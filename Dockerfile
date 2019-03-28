FROM python:latest

# We copy this file first to leverage docker cache
COPY ./requirements.txt /code/pyracms/requirements.txt

WORKDIR /code/pyracms

RUN pip install -r requirements.txt

COPY . /code/pyracms

RUN python setup.py bdist_wheel

