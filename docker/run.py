import argparse
import os
import shutil
import subprocess
import tempfile
import urllib.request

import boto3


S3_RESULTS_INVALID_BUCKET = os.environ.get("S3_RESULTS_INVALID_BUCKET")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run webcompat ML task.")
    parser.add_argument("--issue", action="store", dest="issue")
    parser.add_argument("--file_url", action="store", dest="file_url")
    args = parser.parse_args()

    with urllib.request.urlopen(args.file_url) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(response, tmp_file)
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

    s3 = boto3.resource("s3")
    data = open("predictions.json", "r")
    output_name = "{}.json".format(args.issue)

    s3.Bucket(S3_RESULTS_INVALID_BUCKET).put_object(
        Key=output_name, Body=data, ContentType="application/json"
    )
