module "ec2" {
  source = "terraform-aws-modules/ec2-instance/aws"

  name                        = "${local.name}"
  key_name                    = "${var.key_name}"
  vpc_security_group_ids      = ["${module.security-group.this_security_group_id}"]
  subnet_id                   = "${data.aws_subnet.default.id}"
  ami                         = "${data.aws_ami.ubuntu.id}"
  instance_type               = "${var.instance_type}"
  iam_instance_profile        = "${aws_iam_instance_profile.this.id}"
  associate_public_ip_address = true
  disable_api_termination     = false

  # TODO control elb type, size (20GB, magnetic)

  tags = {
    Name = "${local.name}"
    Type = "stelar-core"
  }
}

resource "aws_eip" "this" {
  vpc      = true
  instance = "${module.ec2.id[0]}"
}

module "security-group" {
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
