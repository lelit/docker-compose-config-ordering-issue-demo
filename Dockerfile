FROM python:2.7

COPY app/requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY ./app/main.py /srv
COPY ./www /srv/www

WORKDIR /srv

CMD python main.py
