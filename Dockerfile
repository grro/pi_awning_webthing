FROM python:3.9.1-alpine

ENV port 9500
ENV name lane

RUN apk add build-base
ADD . /tmp/
WORKDIR /tmp/
RUN  python /tmp/setup.py install
WORKDIR /
RUN rm -r /tmp/

CMD awning --command listen --port $port --filename $filename --name $name



