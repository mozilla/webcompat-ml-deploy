import json
import hashlib
import hmac
import logging
import os
import uuid

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


JOB_DEFINITIONS = os.environ.get("JOB_DEFINITIONS").split(",")
JOB_QUEUE = os.environ.get("JOB_QUEUE")
SECRET = os.environ.get("WEBHOOK_SECRET")


def validate_signature(event):
    """Validate GH event signature"""

    payload = event["body"]
    signature = event["headers"]["X-Hub-Signature"]
    computed_hash = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha1)
    expected = computed_hash.hexdigest().encode()
    received = signature.lstrip("sha1=").encode()
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

    # ignore all actions which are not about
    # 1. removing a label
    # 2. opening an issue
    if hookdata["action"] not in ["unlabeled", "opened"]:
        return {"statusCode": 200, "body": "Skipping event"}

    # for action which are unlabeling, get the name of the label
    if hookdata["action"] == "unlabeled":
        label = hookdata["label"]["name"]
        # ignore all removed labels which are not needs-moderation
        if label != "action-needsmoderation":
            return {"statusCode": 200, "body": "Skipping event"}
    elif hookdata["action"] == "opened":
        # for open actions we are only interested by authenticated users
        sender = hookdata["sender"]["login"]
        if sender == "webcompat-bot":
            return {"statusCode": 200, "body": "Skipping event"}

    # carry-on
    parameters = {"issue_url": hookdata["issue"]["url"]}

    batch = boto3.client(service_name="batch")
    for jobDefinition in JOB_DEFINITIONS:
        logger.debug("Queue: {}".format(JOB_QUEUE))
        logger.debug("Definition: {}".format(jobDefinition))
        logger.debug("Parameters: {}".format(parameters))

        jobName = uuid.uuid4().hex
        job = batch.submit_job(
            jobQueue=JOB_QUEUE,
            jobName=jobName,
            jobDefinition=jobDefinition,
            parameters=parameters,
        )
        logger.debug("Job {} submitted".format(jobName))

    return {"statusCode": 200, "body": json.dumps(job)}
