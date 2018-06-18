variable "ssh_public_key_name" {}

variable "stellar_network_name" {}
variable "zone" {}
variable "instance_type" {}

variable "tld" {}

locals {
  # used to name ec2 and rds instances, security groups, etc.
  stellar_core_name = "stellar-core-${var.stellar_network_name}-${var.zone}"
  horizon_name      = "horizon-${var.stellar_network_name}-${var.zone}"

  # elb name must have length < 32
  horizon_elb_name = "horizon-${var.stellar_network_name}-${random_id.name_suffix.hex}"
}

resource "random_id" "name_suffix" {
  byte_length = 1

  lifecycle {
    create_before_destroy = true
  }
}
