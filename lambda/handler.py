import json
import logging


logger = logging.getLogger(__name__)


def webhook(event, context):
    """Handler for GitHub webhook"""

    try:
        # Parse data from GH event
        hookdata = json.loads(event["body"])
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON")
        return {"body": json.dumps({"error": "JSON decode failure"}), "statusCode": 500}


def invalid(event, context):
    pass
