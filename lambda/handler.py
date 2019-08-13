from io import StringIO

import json
import logging
import os

import boto3
import botocore.vendored.requests as requests


logger = logging.getLogger(__name__)


JOB_NAME = "webcompat_ml_classify"
JOB_DEFINITION = os.environ.get("JOB_DEFINITION")
JOB_QUEUE = os.environ.get("JOB_QUEUE")


def webhook(event, context):
    """Handler for GitHub webhook"""

    try:
        # Parse data from GH event
        hookdata = json.loads(event["body"])
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON")
        return {"body": json.dumps({"error": "JSON decode failure"}), "statusCode": 500}

    io = StringIO()
    json.dump(hookdata, io)

    # Upload tmp csv file
    response = requests.post("https://transfer.sh", data=io)
    parameters = {"file_url": response.content}

    batch = boto3.client(service_name="batch")
    batch.submit_job(
        jobName=JOB_NAME,
        jobQueue=JOB_QUEUE,
        jobDefinition=JOB_DEFINITION,
        parameters=parameters,
    )
