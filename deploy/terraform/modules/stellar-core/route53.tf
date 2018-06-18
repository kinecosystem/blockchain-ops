resource "aws_route53_record" "this" {
  zone_id = "${data.aws_route53_zone.kin.zone_id}"
  name    = "${local.stellar_core_name}.${var.tld}"
  records = ["${module.stellar_core_ec2.public_dns[0]}"]
  type    = "CNAME"
  ttl     = "300"
}
