import argparse
import json
import os
import subprocess
import tempfile
import urllib.request

import boto3

from webcompat_ml.utils.preprocess import prepare_gh_event_invalid


S3_RESULTS_INVALID_BUCKET = os.environ.get("S3_RESULTS_INVALID_BUCKET")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run webcompat ML task.")
    parser.add_argument("--issue-url", action="store", dest="issue_url")
    args = parser.parse_args()

    with urllib.request.urlopen(args.issue_url) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            data = json.load(response)
            df = prepare_gh_event_invalid(data)
            df.to_csv(tmp_file.name, index=False)

            command = [
                "webcompat-ml-invalid",
                "-m",
                "predict",
                "-t",
                "json",
                "-d",
                tmp_file.name,
            ]
            subprocess.run(command, check=True)

    s3 = boto3.client("s3")

    with open("predictions.json", "rb") as prediction:
        output_name = "{}.json".format(args.issue_url.split('/')[-1])
        s3.upload_fileobj(prediction, S3_RESULTS_INVALID_BUCKET, output_name)
