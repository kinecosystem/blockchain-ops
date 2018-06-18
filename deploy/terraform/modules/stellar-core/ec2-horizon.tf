module "horizon_ec2" {
  source                  = "terraform-aws-modules/ec2-instance/aws"
  name                    = "${local.horizon_name}"
  key_name                = "${var.ssh_public_key_name}"
  vpc_security_group_ids  = ["${module.horizon_security_group.this_security_group_id}"]
  subnet_id               = "${data.aws_subnet.default.id}"
  ami                     = "${data.aws_ami.ubuntu.id}"
  instance_type           = "${var.instance_type}"
  disable_api_termination = false

  associate_public_ip_address = true # TODO unncessary, behind elb

  root_block_device = [
    {
      volume_type = "standard" # magnetic
      volume_size = 20
    },
  ]

  tags = {
    Name = "${local.horizon_name}"
    Type = "horizon"
  }
}

module "horizon_security_group" {
  source              = "terraform-aws-modules/security-group/aws"
  name                = "${local.horizon_name}-common"
  description         = "Horizon required ports: PostgreSQL, HTTP/S"
  vpc_id              = "${data.aws_vpc.default.id}"
  ingress_cidr_blocks = ["0.0.0.0/0"]
  ingress_rules       = ["ssh-tcp"]
  egress_cidr_blocks  = ["0.0.0.0/0"]
  egress_rules        = ["postgresql-tcp"]

  egress_with_cidr_blocks = [
    {
      from_port   = 10516
      to_port     = 10516
      protocol    = "tcp"
      description = "DataDog logs intake"
      cidr_blocks = "0.0.0.0/0"
    },
  ]
}

output "horizon_ec2" {
  description = "EC2 public DNS name"
  value       = "${module.horizon_ec2.public_dns[0]}"
}
