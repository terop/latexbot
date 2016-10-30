FROM python:3.5-slim
MAINTAINER Tero Paloheimo <tero.paloheimo@iki.fi>

RUN apt-get update && apt-get install -y texlive dvipng

COPY requirements.txt /usr/local/latexbot/requirements.txt
COPY latexbot.py /usr/local/latexbot/latexbot.py
COPY latexbot.cfg /usr/local/latexbot/latexbot.cfg

WORKDIR /usr/local/latexbot
RUN pip3 install -r requirements.txt

EXPOSE 5000

CMD python3 latexbot.py
