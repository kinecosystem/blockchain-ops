module "horizon" {
  source = "horizon"

  ssh_public_key_name  = "${var.ssh_public_key_name}"
  stellar_network_name = "${var.stellar_network_name}"
  tld                  = "${var.tld}"
  zone                 = "${var.zone}"
  instance_type        = "${var.instance_type}"
  rds_password         = "${var.rds_password}"
  name                 = "${local.horizon_name}"
  elb_name             = "${local.horizon_elb_name}"
}
