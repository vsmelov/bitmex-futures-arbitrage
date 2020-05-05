FROM python:3.8-alpine
RUN apk update && apk add --update alpine-sdk && apk add gcc python3-dev
COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt
RUN mkdir /sources
COPY ./bitmex_futures_arbitrage /sources/bitmex_futures_arbitrage
WORKDIR /sources/bitmex_futures_arbitrage
ENV PYTHONPATH="/sources"
ENTRYPOINT ["python", "main.py"]
