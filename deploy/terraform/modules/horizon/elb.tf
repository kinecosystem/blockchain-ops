resource "aws_elb" "this" {
  name                      = "${var.name}"
  instances                 = ["${aws_instance.this.id}"]
  subnets                   = ["${data.aws_subnet.default.id}"]
  security_groups           = ["${module.elb_security_group.this_security_group_id}"]
  cross_zone_load_balancing = false

  listener = [
    {
      lb_port           = "80"   # listen port
      lb_protocol       = "HTTP"
      instance_port     = "80"   # forward-to port
      instance_protocol = "HTTP"
    },
    {
      lb_port            = "443"
      lb_protocol        = "HTTPS"
      ssl_certificate_id = "${data.aws_acm_certificate.kininfrastructure.arn}"
      instance_port      = "80"
      instance_protocol  = "HTTP"
    },
  ]

  health_check = {
    # target              = "HTTP:8000/status"
    target              = "HTTP:80/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    type            = "horizon"
    stellar-network = "${var.stellar_network_name}"
  }
}

module "elb_security_group" {
  source              = "terraform-aws-modules/security-group/aws"
  name                = "${var.name}-elb"
  description         = "Horizon required ports: PostgreSQL, HTTP/S"
  vpc_id              = "${data.aws_vpc.default.id}"
  ingress_cidr_blocks = ["0.0.0.0/0"]
  ingress_rules       = ["http-80-tcp", "https-443-tcp"]
  egress_cidr_blocks  = ["0.0.0.0/0"]
  egress_rules        = ["http-80-tcp"]

  egress_with_cidr_blocks = [
    {
      from_port   = 8000
      to_port     = 8000
      protocol    = "tcp"
      description = "Horizon health check"
      cidr_blocks = "0.0.0.0/0"
    },
  ]
}

output "elb" {
  description = "ELB DNS name"
  value       = "${aws_elb.this.dns_name}"
}

data "aws_acm_certificate" "kininfrastructure" {
  domain   = "*.kininfrastructure.com"
  statuses = ["ISSUED"]
}
