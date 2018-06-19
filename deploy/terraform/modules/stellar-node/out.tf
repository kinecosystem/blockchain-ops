# stellar-core

output "route53_stellar_core" {
  description = "Route53 FQDN name assigned to the EC2 instance"
  value       = "${module.stellar_core.route53}"
}

output "s3_bucket_stellar_core" {
  description = "S3 bucket name"
  value       = "${module.stellar_core.s3}"
}

output "rds_stellar_core" {
  description = "RDS address"
  value       = "${module.stellar_core.rds}"
}

# horizon

output "route53_horizon" {
  description = "Route53 FQDN name assigned to the EC2 instance"
  value       = "${module.horizon.route53}"
}

output "ec2_horizon" {
  description = "EC2 public DNS name"
  value       = "${module.horizon.ec2}"
}

output "rds_horizon" {
  description = "RDS address"
  value       = "${module.horizon.rds}"
}
