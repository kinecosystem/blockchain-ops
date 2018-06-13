# data sources to get vpc, subnet, and ami details

data "aws_vpc" "default" {
  default = true
}

data "aws_subnet" "default" {
  vpc_id            = "${data.aws_vpc.default.id}"
  availability_zone = "${var.zone}"
  default_for_az    = true
}

data "aws_ami" "ubuntu" {
  most_recent = true

  owners = ["099720109477"] # canonical/ubuntu

  filter {
    name = "name"

    values = [
      "ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-*",
    ]
  }
}
