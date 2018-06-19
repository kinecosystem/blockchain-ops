output "route53" {
  description = "Route53 FQDN name assigned to the EC2 instance"
  value       = "${aws_route53_record.this.fqdn}"
}

output "s3" {
  description = "S3 bucket name"
  value       = "${aws_s3_bucket.this.id}"
}

output "rds" {
  description = "RDS address"
  value       = "${module.rds.this_db_instance_address}"
}
