variable "access_key" {}
variable "secret_key" {}

variable "stellar_network_name" {}
variable "zone" {}
variable "key_name" {}
variable "instance_type" {}

variable "tld" {}

locals {
  # used to name ec2 and rds instances, security groups, etc.
  name = "stellar-core-${var.stellar_network_name}-${var.zone}"
}
