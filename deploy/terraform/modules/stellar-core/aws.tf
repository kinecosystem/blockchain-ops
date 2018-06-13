provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region     = "${substr(var.zone, 0, length(var.zone)-1)}"
}
