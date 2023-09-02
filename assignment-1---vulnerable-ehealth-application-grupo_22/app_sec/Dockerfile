FROM ubuntu:20.04

WORKDIR /app

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

RUN apt-get update
RUN apt-get install -y libmysqlclient-dev
RUN apt-get install -y python3-pip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

EXPOSE 5000
COPY . .
CMD ["flask", "run"]