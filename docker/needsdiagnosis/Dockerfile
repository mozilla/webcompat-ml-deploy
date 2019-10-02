FROM python:3.7

RUN pip install git+git://github.com/mozilla/webcompat-ml@master#egg=webcompat_ml
RUN pip install boto3 certifi "elasticsearch>=6.0.0,<7.0.0"

ARG MODEL_PATH

WORKDIR /app
COPY run.py /app/
COPY $MODEL_PATH /srv/model.bin