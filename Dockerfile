FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


FROM python:3.11-slim

ENV port=9040 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels requirements.txt

COPY *.py ./

CMD ["sh", "-c", "python awning_webthing.py $port $filename $chip $switch_pin_forward $switch_pin_backward"]
