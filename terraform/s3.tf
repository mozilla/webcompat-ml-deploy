resource "aws_s3_bucket" "webcompat_ml_results" {
  bucket = "webcompat-ml-results"
  acl    = "public-read"

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
  ]
}
EOF
}
