resource "aws_s3_bucket" "webcompat_ml_results" {
    bucket = "webcompat-ml-results"
    acl    = "public-read"
}
