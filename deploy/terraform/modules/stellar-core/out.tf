output "route53" {
  description = "Route53 FQDN name assigned to the EC2 instance"
  value       = "${aws_route53_record.this.fqdn}"
}

output "instance_tags" {
  description = "List of tags"
  value       = "${module.ec2.tags}"
}

output "s3" {
  description = "S3 bucket name"
  value       = "${aws_s3_bucket.this.id}"
}
