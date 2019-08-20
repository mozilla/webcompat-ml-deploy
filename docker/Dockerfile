FROM python:3.7

WORKDIR /app
COPY run.py /app/
RUN pip install git+git://github.com/mozilla/webcompat-ml@master#egg=webcompat_ml
RUN pip install boto3
