# Security groups setup
resource "aws_security_group" "webcompat-ml-sg" {
  name        = "webcompat-ml-security-group"
  description = "Webcompat ML - Security Group"
  vpc_id      = "${data.aws_vpc.default.id}"

  egress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
