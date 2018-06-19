module "horizon" {
  source = "horizon"

  instance_key_pair_name = "${var.instance_key_pair_name}"
  ssh_private_key        = "${var.ssh_private_key}"
  stellar_network_name   = "${var.stellar_network_name}"
  tld                    = "${var.tld}"
  zone                   = "${var.zone}"
  instance_type          = "${var.instance_type}"
  rds_password           = "${var.rds_password}"
  name                   = "${local.horizon_name}"
  elb_name               = "${local.horizon_elb_name}"
}
