resource "aws_route53_record" "this" {
  zone_id = "${data.aws_route53_zone.kin.zone_id}"
  name    = "${local.stellar_core_name}.${var.tld}"
  type    = "CNAME"
  ttl     = "300"

  records = ["${module.ec2.public_dns[0]}"]
}
