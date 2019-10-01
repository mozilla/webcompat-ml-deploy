resource "aws_s3_bucket" "webcompat_ml_results" {
  bucket = "webcompat-ml-results"
  acl    = "public-read"

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
  }

  website {
    index_document = "index.html"
    error_document = "error.html"
  }

  policy = <<EOF
{
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "*"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::webcompat-ml-results/*"
    }
  ],
  "Version": "2008-10-17"
}
EOF
}
