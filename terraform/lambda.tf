data "archive_file" "webcompat_ml" {
  type = "zip"
  source_file = "../lambda/handler.py"
  output_path = "lambda_handler.zip"
}

resource "aws_lambda_function" "webhook" {
  function_name = "WebcompatMLWebhookHandler"
  handler = "handler.webhook"
  runtime = "python3.7"
  filename = "lambda_handler.zip"
  source_code_hash = "${data.archive_file.webcompat_ml.output_base64sha256}"
  role = "${aws_iam_role.webcompat_ml_lambda.arn}"
  environment {
    variables = {
      JOB_DEFINITION = "${aws_batch_job_definition.webcompat_classification.name}"
      JOB_QUEUE = "${aws_batch_job_queue.webcompat-classify.name}"
    }
  }
}
