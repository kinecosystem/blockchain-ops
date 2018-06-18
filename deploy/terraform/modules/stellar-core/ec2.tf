module "ec2" {
  source = "terraform-aws-modules/ec2-instance/aws"

  name                   = "${local.name}"
  key_name               = "${var.key_name}"
  vpc_security_group_ids = ["${module.ec2-security-group.this_security_group_id}"]
  subnet_id              = "${data.aws_subnet.default.id}"
  ami                    = "${data.aws_ami.ubuntu.id}"
  instance_type          = "${var.instance_type}"

  iam_instance_profile = "${aws_iam_instance_profile.this.id}"

  associate_public_ip_address = true
  disable_api_termination     = false

  root_block_device = [
    {
      volume_type = "standard" # magnetic
      volume_size = 20
    },
  ]

  tags = {
    Name = "${local.name}"
    Type = "stelar-core"
  }
}

resource "aws_eip" "this" {
  vpc      = true
  instance = "${module.ec2.id[0]}"
}

module "ec2-security-group" {
  source = "terraform-aws-modules/security-group/aws"

  name        = "${local.name}-common"
  description = "Stellar Core requires ports: stellar-core P2P, PostgreSQL, HTTP/S"

  vpc_id              = "${data.aws_vpc.default.id}"
  ingress_cidr_blocks = ["0.0.0.0/0"]
  ingress_rules       = ["ssh-tcp"]
  egress_cidr_blocks  = ["0.0.0.0/0"]
  egress_rules        = ["postgresql-tcp", "http-80-tcp", "https-443-tcp"]

  ingress_with_cidr_blocks = [
    {
      from_port   = 11625
      to_port     = 11625
      protocol    = "tcp"
      description = "Stellar Core P2P IPv4"
      cidr_blocks = "0.0.0.0/0"
    },
  ]

  egress_with_cidr_blocks = [
    {
      from_port   = 11625
      to_port     = 11625
      protocol    = "tcp"
      description = "Stellar Core P2P IPv4"
      cidr_blocks = "0.0.0.0/0"
    },
    {
      from_port   = 10516
      to_port     = 10516
      protocol    = "tcp"
      description = "DataDog logs intake"
      cidr_blocks = "0.0.0.0/0"
    },
  ]
}

# data sources to get vpc, subnet, ami, route53 details

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

data "aws_route53_zone" "kin" {
  name = "kininfrastructure.com."
}
