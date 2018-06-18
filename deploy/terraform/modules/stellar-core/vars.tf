variable "access_key" {}
variable "secret_key" {}

variable "stellar_network_name" {}
variable "zone" {}
variable "ssh_public_key" {}
variable "instance_type" {}

variable "tld" {}

locals {
  # used to name ec2 and rds instances, security groups, etc.
  name = "stellar-core-${var.stellar_network_name}-${var.zone}"

  # ssh key to create for accessing ec2 instances
  ssh_public_key_name = "stellar-core-${var.stellar_network_name}"
}
