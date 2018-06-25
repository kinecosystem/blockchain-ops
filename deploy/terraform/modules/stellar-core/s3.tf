resource "aws_s3_bucket" "this" {
  bucket = "${var.name}"
  policy = "${data.aws_iam_policy_document.ec2_s3_bucket_public_read_access.json}"

  # https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html
  acl = "public-read"
}

data "aws_iam_policy_document" "ec2_s3_bucket_public_read_access" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::${var.name}/*"]

    principals = {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

output "s3" {
  description = "S3 bucket name"
  value       = "${aws_s3_bucket.this.id}"
}
