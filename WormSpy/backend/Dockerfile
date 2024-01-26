FROM python:3.9

ENV APP_DIR=/var/opt/wormspy
RUN mkdir -p ${APP_DIR}
WORKDIR ${APP_DIR}

COPY ./code/requirements.txt ${APP_DIR}/requirements.txt

RUN apt-get update
RUN apt-get install -y build-essential

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt 

ENV FLASK_APP app.py
ENV FLASK_DEBUG 1
ENV FLASK_ENV development
ENV FLASK_RUN_HOST 0.0.0.0

CMD [ "python", "-m", "flask", "run", "--host=0.0.0.0" ]