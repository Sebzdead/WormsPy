FROM python:3.8-slim

ENV APP_DIR=/var/opt/wormspy
RUN mkdir -p ${APP_DIR}
WORKDIR ${APP_DIR}

RUN apt-get update
RUN apt-get install -y build-essential

RUN pip3 install --upgrade pip
RUN pip3 install Flask Flask-Cors
RUN pip3 install opencv-python

ENV FLASK_APP server.py
ENV FLASK_DEBUG 1
ENV FLASK_ENV development
ENV FLASK_RUN_HOST 0.0.0.0

CMD [ "python", "-m", "flask", "run", "--host=0.0.0.0" ]