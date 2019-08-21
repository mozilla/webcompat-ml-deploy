import json
import hashlib
import hmac
import logging
import os

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


JOB_NAME = "webcompat_ml_classify"
JOB_DEFINITION = os.environ.get("JOB_DEFINITION")
JOB_QUEUE = os.environ.get("JOB_QUEUE")
SECRET = os.environ.get("WEBHOOK_SECRET")


def validate_signature(event):
    """Validate GH event signature"""

    payload = event["body"]
    signature = event["headers"]["X-Hub-Signature"]
    computed_hash = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha1)
    expected = computed_hash.hexdigest().encode()
    received = signature.lsplit('sha1=').encode()
    return hmac.compare_digest(expected, received)


def webhook(event, context):
    """Handler for GitHub webhook"""

    logger.debug("Event: {}".format(event))

    if not validate_signature(event):
        return {"statusCode": 403, "body": "Signature doesn't match."}

    try:
        # Parse data from GH event
        hookdata = json.loads(event["body"])
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON")
        return {"body": json.dumps({"error": "JSON decode failure"}), "statusCode": 500}

    parameters = {"issue_url": hookdata["issue"]["url"]}

    batch = boto3.client(service_name="batch")
    job = batch.submit_job(
        jobName=JOB_NAME,
        jobQueue=JOB_QUEUE,
        jobDefinition=JOB_DEFINITION,
        parameters=parameters,
    )

    return {"statusCode": 200, "body": json.dumps(job)}
