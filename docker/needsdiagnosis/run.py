import argparse
import json
import os
import pandas
import subprocess
import tempfile
import urllib.request
import urllib.urlencode

from datetime import datetime
from distutils.util import strtobool

import boto3

from elasticsearch import Elasticsearch


MODEL_PATH = "/srv/model.bin"
PREDICTION_PATH = "/srv/predictions.csv"
JSON_OUTPUT_PATH = "/srv/predictions.json"
S3_RESULTS_ML_BUCKET = os.environ.get("S3_RESULTS_ML_BUCKET")
ES = Elasticsearch(os.environ.get("ES_URL"))
GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN")
AUTO_CLOSE_ISSUES = strtobool(os.environ.get("AUTO_CLOSE_ISSUES", "False"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run webcompat ML task.")
    parser.add_argument("--issue-url", action="store", dest="issue_url")
    args = parser.parse_args()

    print("Issue to fetch: {}".format(args.issue_url))
    with urllib.request.urlopen(args.issue_url) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            data = json.load(response)
            issue = {"body": data["body"], "title": data["title"]}
            df = pandas.DataFrame([issue])

            df.to_csv(tmp_file.name, index=False)

            command = [
                "webcompat-ml-needsdiagnosis",
                "predict",
                "--data",
                tmp_file.name,
                "--model",
                MODEL_PATH,
                "--output",
                PREDICTION_PATH,
            ]

            print("Running command: {}".format(command))

            subprocess.run(command, check=True)

    df = pandas.read_csv(PREDICTION_PATH)
    df.to_json(JSON_OUTPUT_PATH)

    s3 = boto3.client("s3")
    issue_number = args.issue_url.split("/")[-1]

    print("Writing json output to S3")
    with open(JSON_OUTPUT_PATH, "rb") as prediction:
        output_name = "needsdiagnosis/{}.json".format(issue_number)
        s3.upload_fileobj(
            prediction,
            S3_RESULTS_ML_BUCKET,
            output_name,
            ExtraArgs={"ContentType": "application/json"},
        )

    print("Indexing results to ES")
    with open(JSON_OUTPUT_PATH, "rb") as prediction:
        prediction = json.load(prediction)
        doc = {
            "issue": int(issue_number),
            "issue_url": args.issue_url,
            "predicted_at": datetime.now(),
            "prediction": prediction,
        }

        ES.indices.create("needsdiagnosis-ml-results", ignore=400)
        ES.index(
            index="needsdiagnosis-ml-results",
            doc_type="needsdiagnosis-result",
            id=int(issue_number),
            body=doc,
        )

    # Add labels and automatically close issues
    needsdiagnosis = prediction["needsdiagnosis"][0]
    proba = prediction["proba_False"][0]
    is_anonymous = (
        "Submitted in the name of" not in data["body"]
        and data["user"]["login"] == "webcompat-bot"
    )

    if not needsdiagnosis and is_anonymous:
        labels_url = "{}/{}".format(args.issue_url, "labels")
        headers = ({"Authorization": "token {}".format(GITHUB_API_TOKEN)},)

        if proba > 0.9:
            print("Adding label to issue")
            labels_data = urllib.urlencode({"labels": ["ml-needsdiagnosis"]})
            req = urllib.request.Request(
                url=labels_url, data=labels_data, headers=headers, method="POST"
            )
            urllib.request.urlopen(req)

        if proba > 0.95:
            # Update labels
            labels_data = urllib.urlencode({"labels": ["ml-proba-high"]})
            req = urllib.request.Request(
                url=labels_url, data=labels_data, headers=headers, method="POST"
            )
            urllib.request.urlopen(req)

            # Close issue
            if AUTO_CLOSE_ISSUES:
                close_data = urllib.urlencode({"state": "closed"})
                req = urllib.request.Request(
                    url=args.issue_url, data=close_data, headers=headers, method="PATCH"
                )
                urllib.request.urlopen(req)
