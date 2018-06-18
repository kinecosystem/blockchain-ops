resource "aws_route53_record" "horizon" {
  zone_id = "${data.aws_route53_zone.kin.zone_id}"
  name    = "${local.horizon_name}.${var.tld}"
  records = ["${aws_elb.horizon.dns_name}"]
  type    = "CNAME"
  ttl     = "300"
}

output "horizon_route53" {
  description = "Route53 FQDN name assigned to the EC2 instance"
  value       = "${aws_route53_record.horizon.fqdn}"
}
