# AWS Lambda
data "archive_file" "webcompat_ml" {
  type        = "zip"
  source_file = "../lambda/handler.py"
  output_path = "lambda_handler.zip"
}

resource "random_password" "webhook_secret" {
  length  = 16
  special = false
}

resource "aws_lambda_function" "webcompat_ml_webhook" {
  function_name    = "WebcompatMLWebhookHandler"
  handler          = "handler.webhook"
  runtime          = "python3.7"
  filename         = "lambda_handler.zip"
  source_code_hash = "${data.archive_file.webcompat_ml.output_base64sha256}"
  role             = "${aws_iam_role.webcompat_ml_lambda.arn}"

  environment {
    variables = {
      JOB_DEFINITION = "${aws_batch_job_definition.webcompat_classification.name}:${aws_batch_job_definition.webcompat_classification.revision}"
      JOB_QUEUE      = "${aws_batch_job_queue.webcompat-classify.name}"
      WEBHOOK_SECRET = "${random_password.webhook_secret.result}"
    }
  }

  lifecycle {
    ignore_changes = [
      environment.0.variables.WEBHOOK_SECRET,
    ]
  }
}

# AWS API gateway for lambda
resource "aws_api_gateway_rest_api" "webcompat_ml_webhook" {
  name        = "WebcompatMLWebhookAPI"
  description = "Endpoint for the webcompat ML API webhook"
}

resource "aws_api_gateway_resource" "webcompat_ml_webhook" {
  rest_api_id = "${aws_api_gateway_rest_api.webcompat_ml_webhook.id}"
  parent_id   = "${aws_api_gateway_rest_api.webcompat_ml_webhook.root_resource_id}"
  path_part   = "webcompat_ml_webhook"
}

resource "aws_api_gateway_method" "webcompat_ml_webhook" {
  rest_api_id   = "${aws_api_gateway_rest_api.webcompat_ml_webhook.id}"
  resource_id   = "${aws_api_gateway_resource.webcompat_ml_webhook.id}"
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "webcompat_ml_lambda" {
  rest_api_id = "${aws_api_gateway_rest_api.webcompat_ml_webhook.id}"
  resource_id = "${aws_api_gateway_method.webcompat_ml_webhook.resource_id}"
  http_method = "${aws_api_gateway_method.webcompat_ml_webhook.http_method}"

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "${aws_lambda_function.webcompat_ml_webhook.invoke_arn}"
}

resource "aws_api_gateway_deployment" "webcompat_ml_webhook" {
  depends_on = [
    "aws_api_gateway_integration.webcompat_ml_lambda",
  ]

  rest_api_id = "${aws_api_gateway_rest_api.webcompat_ml_webhook.id}"
  stage_name  = "webhook"
}

# AWS Lambda permissions
resource "aws_lambda_permission" "webcompat_ml_webhook_apigateway" {
  statement_id  = "AllowWebcompatMLAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.webcompat_ml_webhook.arn}"
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_deployment.webcompat_ml_webhook.execution_arn}/*/*"
}
