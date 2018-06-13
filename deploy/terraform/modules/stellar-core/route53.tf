resource "aws_route53_record" "this" {
  zone_id = "${data.aws_route53_zone.kin.zone_id}"
  name    = "${local.name}.${var.tld}"
  type    = "CNAME"
  ttl     = "300"

  # records = ["${aws_eip.public_ip}"]
  records = ["${module.ec2.public_dns[0]}"]
}
