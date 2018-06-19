resource "aws_s3_bucket" "this" {
  bucket = "${var.name}"
  acl    = "public-read"
}
