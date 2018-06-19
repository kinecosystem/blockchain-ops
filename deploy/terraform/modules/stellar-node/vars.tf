variable "instance_key_pair_name" {}
variable "ssh_private_key" {}

variable "stellar_network_name" {}
variable "zone" {}
variable "instance_type" {}

variable "rds_password" {}

variable "tld" {}

locals {
  # used to name ec2 and rds instances, security groups, etc.
  stellar_core_name = "stellar-core-${var.stellar_network_name}-${random_id.name_suffix.hex}"
  horizon_name      = "horizon-${var.stellar_network_name}-${random_id.name_suffix.hex}"
}

resource "random_id" "name_suffix" {
  byte_length = 2

  lifecycle {
    create_before_destroy = true
  }
}
