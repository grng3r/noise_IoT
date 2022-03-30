#noise_alpine:1.0 image
#To build it docker build -f Dockerfile -t nose_alpine:1.0 .
#To run -> docker run  --name noise_alpine -it noise_alpine:1.0 
#Second terminal docker exec -it noise_alpine bash

FROM python:3.8-alpine3.15

#Change shell to bash in order to use source command

RUN apk update && \
    apk add --no-cache --upgrade bash && \
    apk add build-base && \
    apk add libffi-dev && \
    apk add --no-cache git && \
    apk add tcpdump && \
    mkdir /app

SHELL ["/bin/bash", "-c"]

#COPY venv /app/venv
COPY requirements.txt /app/requirements.txt

RUN apk add py3-pip && \
	python3 -m pip install scapy-python3

WORKDIR /app

COPY cli.py /app/cly.py
COPY server.py /app/server.py


RUN python3 -m pip install -r requirements.txt

ENTRYPOINT ["bash"]

#RUN python3 -m venv venv && \
#    source venv/bin/activate
