resource "aws_s3_bucket" "this" {
  bucket = "${var.name}"
  acl    = "public-read"
}

output "s3" {
  description = "S3 bucket name"
  value       = "${aws_s3_bucket.this.id}"
}
