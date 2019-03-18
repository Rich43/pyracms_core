FROM python:latest

EXPOSE 6543/tcp

# We copy this file first to leverage docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

RUN python setup.py install

RUN initialize_pyracms_db production.ini

ENTRYPOINT [ "pserve" ]

CMD [ "production.ini" ]

