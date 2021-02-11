FROM python:2.7.18-alpine3.11

RUN  mkdir -p /kvstore/server/
COPY start requirements.txt /kvstore/
COPY server/ /kvstore/server/
RUN  cd /kvstore && pip install -r requirements.txt

WORKDIR  /kvstore
ENTRYPOINT ["./start"]
