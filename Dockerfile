FROM python:3.9.1-alpine

ENV port 9500

RUN apk add build-base

ADD setup.py /tmp/.
ADD README.md /tmp/.
ADD pi_awning_webthing /tmp/pi_awning_webthing/.

RUN ls /tmp/
WORKDIR /tmp/
RUN  python /tmp/setup.py install
WORKDIR /
RUN rm -r /tmp/

CMD awning --command listen --port $port --filename $filename



