resource "aws_s3_bucket" "this" {
  bucket = "${local.stellar_core_name}"
  acl    = "public-read"
}
