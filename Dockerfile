FROM python:3

ENV port 8080

RUN cd /etc
RUN mkdir app
WORKDIR /etc/app
ADD *.py /etc/app/
ADD requirements.txt /etc/app/.
RUN pip install -r requirements.txt

CMD python /etc/app/awning_webthing.py.py $port $filename $switch_pin_forward -$switch_pin_backward




