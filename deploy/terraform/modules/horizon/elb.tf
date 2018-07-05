module "alb" {
  source = "terraform-aws-modules/alb/aws"

  load_balancer_name = "${var.name}"
  vpc_id             = "${data.aws_vpc.default.id}"
  logging_enabled    = false

  # use the subnet in the zone we deploy horizon, plus a subnet from another zone (alb requires at least 2 subnets).
  #
  # the scary interpolation does the following:
  #  - create a list with data.aws_subnet.default.id first by concatenating [data.aws_subnet.default.id] + [subnet 1, subnet 2, ...]
  #  - make all items unique (distinct) by filtering duplicate occurences of data.aws_subnet.default.id
  #  - the result will be a list starting with the data.aws_subnet.default.id, followed by all other subnet itds
  #  - pick the second item, which must be another subnet id
  subnets = ["${data.aws_subnet.default.id}", "${element(distinct(concat(list(data.aws_subnet.default.id), data.aws_subnet_ids.default.ids)), 1)}"]

  security_groups = ["${module.alb_security_group.this_security_group_id}"]

  http_tcp_listeners = [
    {
      port     = "80"
      protocol = "HTTP"
    },
  ]

  http_tcp_listeners_count = "1"

  https_listeners = [
    {
      port            = "443"
      protocol        = "HTTPS"
      certificate_arn = "${data.aws_acm_certificate.kininfrastructure.arn}"
    },
  ]

  https_listeners_count = "1"

  target_groups = [
    {
      name             = "${var.name}"
      backend_protocol = "HTTP"
      backend_port     = 80

      health_check_interval            = 30
      health_check_timeout             = 5
      health_check_healthy_threshold   = 3
      health_check_unhealthy_threshold = 3
      health_check_matcher             = "200"
      stickiness_enabled               = true
      target_type                      = "instance"

      health_check_path = "/"
      health_check_port = "80"

      # health_check_path                = "/status"
      # health_check_port                = "8000"
    },
  ]

  target_groups_count = "1"

  tags = {
    type            = "horizon"
    stellar-network = "${var.stellar_network_name}"
  }
}

resource "aws_lb_target_group_attachment" "this" {
  target_group_arn = "${module.alb.target_group_arns[0]}"
  target_id        = "${aws_instance.this.id}"
  port             = 80
}

module "alb_security_group" {
  source              = "terraform-aws-modules/security-group/aws"
  name                = "${var.name}-alb"
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

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = "${module.alb.dns_name}"
}

output "alb_zone_id" {
  description = "ALB Zone ID"
  value       = "${module.alb.load_balancer_zone_id}"
}

data "aws_acm_certificate" "kininfrastructure" {
  domain   = "*.kininfrastructure.com"
  statuses = ["ISSUED"]
}

data "aws_subnet_ids" "default" {
  vpc_id = "${data.aws_vpc.default.id}"
}
